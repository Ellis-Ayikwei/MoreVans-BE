"""the StripeService class provides methods to interact with Stripe's API for payment processing, including creating checkout sessions, handling webhooks, and managing refunds."""

# apps/Payment/stripe_service.py

import stripe
import logging
from typing import Dict, Optional, List, Any
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from .models import Payment, PaymentMethod, StripeEvent
from apps.User.models import User
from apps.Request.models import Request

logger = logging.getLogger(__name__)


class StripeService:
    """
    Service class to handle Stripe Checkout and webhook operations
    """

    def __init__(self):
        # Set Stripe API key from settings
        stripe.api_key = getattr(settings, "STRIPE_SECRET_KEY", "")
        self.webhook_endpoint_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")

    def create_checkout_session(
        self,
        amount: Decimal,
        currency: str,
        user: User,
        request_obj: Request,
        success_url: str,
        cancel_url: str,
        description: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Create a Stripe Checkout Session
        """
        try:
            # Convert amount to cents (Stripe requires amount in smallest currency unit)
            amount_cents = int(amount * 100)

            # Prepare metadata to track the request and user
            metadata = {
                "user_id": str(user.id),
                "request_id": str(request_obj.id),
                "platform": "morevans",
            }

            # Create checkout session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": currency.lower(),
                            "product_data": {
                                "name": description
                                or f"MoreVans Service - Request #{request_obj.id}",
                                "description": f"Payment for moving service request {request_obj.id}",
                            },
                            "unit_amount": amount_cents,
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=user.email,
                metadata=metadata,
                # Optional: Create customer for future payments
                customer_creation="if_required",
                # Optional: Allow promotion codes
                allow_promotion_codes=True,
                # Optional: Collect billing address
                billing_address_collection="required",
            )

            # Create a payment record in pending status
            Payment.objects.create(
                request=request_obj,
                amount=amount,
                currency=currency.upper(),
                status="pending",
                payment_type="full_payment",
                description=description or f"Payment for request {request_obj.id}",
                transaction_id=checkout_session.id,  # Use session ID as transaction ID
                metadata=metadata,
            )

            logger.info(
                f"Created checkout session {checkout_session.id} for user {user.id}"
            )
            return {
                "id": checkout_session.id,
                "url": checkout_session.url,
                "status": checkout_session.status,
                "amount": amount,
                "currency": currency,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            return None

    def create_refund(
        self,
        payment_intent_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Create a refund for a payment
        """
        try:
            refund_params = {
                "payment_intent": payment_intent_id,
                "metadata": {
                    "platform": "morevans",
                    "reason": reason or "Customer request",
                },
            }

            if amount:
                refund_params["amount"] = int(amount * 100)  # Convert to cents

            refund = stripe.Refund.create(**refund_params)

            logger.info(
                f"Created refund {refund.id} for payment intent {payment_intent_id}"
            )
            return {
                "id": refund.id,
                "amount": Decimal(refund.amount) / 100,  # Convert back from cents
                "status": refund.status,
                "reason": refund.reason,
            }

        except stripe.error.StripeError as e:
            logger.error(
                f"Error creating refund for payment intent {payment_intent_id}: {str(e)}"
            )
            return None

    def retrieve_checkout_session(self, session_id: str) -> Optional[Dict]:
        """
        Retrieve a checkout session from Stripe
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return {
                "id": session.id,
                "status": session.status,
                "payment_status": session.payment_status,
                "amount_total": (
                    Decimal(session.amount_total) / 100
                    if session.amount_total
                    else None
                ),
                "currency": session.currency,
                "customer_email": session.customer_email,
                "metadata": session.metadata,
                "payment_intent": session.payment_intent,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving checkout session {session_id}: {str(e)}")
            return None

    def handle_webhook_event(self, payload: str, sig_header: str) -> Optional[Dict]:
        """
        Handle Stripe webhook events
        """
        print("about to hanlde webhook event")
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_endpoint_secret
            )
            print("the event is", event)
        except ValueError:
            logger.error("Invalid payload in webhook")
            return None
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid signature in webhook")
            return None

        # Check if event already processed
        stripe_event, created = StripeEvent.objects.get_or_create(
            stripe_event_id=event["id"],
            defaults={"event_type": event["type"], "processed": False},
        )

        if not created and stripe_event.processed:
            logger.info(f"Event {event['id']} already processed")
            return {"status": "already_processed"}
        print("b=noe thr event", event)
        # Process the event
        result = self._process_webhook_event(event)
        print("the stripe web hook event result is", result)

        # Mark event as processed
        stripe_event.processed = True
        stripe_event.processed_at = timezone.now()
        stripe_event.save()

        return result

    def _process_webhook_event(self, event: Dict) -> Dict:
        """
        Process different types of webhook events
        """
        event_type = event["type"]
        event_data = event["data"]["object"]

        logger.info(f"Processing webhook event: {event_type}")

        if event_type == "checkout.session.completed":
            return self._handle_checkout_completed(event_data)
        elif event_type == "payment_intent.succeeded":
            return self._handle_payment_succeeded(event_data)
        elif event_type == "payment_intent.payment_failed":
            return self._handle_payment_failed(event_data)
        elif event_type == "charge.dispute.created":
            return self._handle_chargeback_created(event_data)
        elif event_type == "charge.refunded":
            return self._handle_refund_completed(event_data)
        else:
            logger.info(f"Unhandled event type: {event_type}")
            return {"status": "unhandled"}

    def _handle_checkout_completed(self, session: Dict) -> Dict:
        """
        Handle completed checkout session
        """
        try:
            session_id = session["id"]
            metadata = session.get("metadata", {})
            request_id = metadata.get("request_id")

            if not request_id:
                logger.error(f"No request_id in session metadata: {session_id}")
                return {"status": "error", "message": "No request_id in metadata"}

            # Find the payment record
            try:
                payment = Payment.objects.get(
                    transaction_id=session_id, request_id=request_id
                )
            except Payment.DoesNotExist:
                logger.error(f"Payment not found for session {session_id}")
                return {"status": "error", "message": "Payment not found"}

            # Update payment status
            payment.status = "completed"
            payment.completed_at = timezone.now()
            payment.stripe_payment_intent_id = session.get("payment_intent")
            payment.save()

            # Update request status to confirmed
            request_obj = payment.request
            if request_obj.status != "confirmed":
                request_obj.status = "confirmed"
                request_obj.save()

                # TODO: Create job from request or trigger business logic
                logger.info(f"Request {request_obj.id} confirmed after payment")

            logger.info(f"Checkout completed for request {request_obj.id}")
            return {"status": "success", "payment_id": payment.id}

        except Exception as e:
            logger.error(f"Error handling checkout completion: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _handle_payment_succeeded(self, payment_intent: Dict) -> Dict:
        """
        Handle successful payment (backup for checkout.session.completed)
        """
        try:
            payment_intent_id = payment_intent["id"]

            # Find payment by payment intent ID
            payment = Payment.objects.filter(
                stripe_payment_intent_id=payment_intent_id
            ).first()

            if payment and payment.status != "completed":
                payment.status = "completed"
                payment.completed_at = timezone.now()
                payment.save()

                logger.info(f"Payment intent succeeded for payment {payment.id}")

            return {"status": "success"}

        except Exception as e:
            logger.error(f"Error handling payment success: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _handle_payment_failed(self, payment_intent: Dict) -> Dict:
        """
        Handle failed payment
        """
        try:
            payment_intent_id = payment_intent["id"]

            # Find payment by payment intent ID
            payment = Payment.objects.filter(
                stripe_payment_intent_id=payment_intent_id
            ).first()

            if payment:
                payment.status = "failed"
                payment.failed_at = timezone.now()
                payment.failure_reason = payment_intent.get(
                    "last_payment_error", {}
                ).get("message", "Payment failed")
                payment.save()

                logger.info(f"Payment failed for payment {payment.id}")

            return {"status": "success"}

        except Exception as e:
            logger.error(f"Error handling payment failure: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _handle_refund_completed(self, charge: Dict) -> Dict:
        """
        Handle completed refund
        """
        try:
            payment_intent_id = charge.get("payment_intent")
            refund_amount = Decimal(charge.get("amount_refunded", 0)) / 100

            if payment_intent_id:
                payment = Payment.objects.filter(
                    stripe_payment_intent_id=payment_intent_id
                ).first()

                if payment:
                    # Check if full or partial refund
                    if refund_amount >= payment.amount:
                        payment.status = "refunded"
                    else:
                        payment.status = "partially_refunded"

                    payment.refunded_at = timezone.now()
                    payment.save()

                    logger.info(f"Refund completed for payment {payment.id}")

            return {"status": "success"}

        except Exception as e:
            logger.error(f"Error handling refund completion: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _handle_chargeback_created(self, charge: Dict) -> Dict:
        """
        Handle chargeback/dispute creation
        """
        try:
            payment_intent_id = charge.get("payment_intent")

            if payment_intent_id:
                payment = Payment.objects.filter(
                    stripe_payment_intent_id=payment_intent_id
                ).first()

                if payment:
                    # Add metadata about the dispute
                    payment.metadata = payment.metadata or {}
                    payment.metadata["dispute_created"] = True
                    payment.metadata["dispute_date"] = timezone.now().isoformat()
                    payment.save()

                    logger.warning(f"Chargeback created for payment {payment.id}")

            return {"status": "success"}

        except Exception as e:
            logger.error(f"Error handling chargeback: {str(e)}")
            return {"status": "error", "message": str(e)}
