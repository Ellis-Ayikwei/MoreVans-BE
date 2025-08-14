"""the StripeService class provides methods to interact with Stripe's API for payment processing, including creating checkout sessions, handling webhooks, managing refunds, and polling payment status."""

# apps/Payment/stripe_service.py

import stripe
import logging
import time
from typing import Dict, Optional, List, Any, Tuple
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from .models import Payment, PaymentMethod, StripeEvent
from apps.User.models import User
from apps.Request.models import Request

logger = logging.getLogger(__name__)


class StripePollingException(Exception):
    """Custom exception for polling-related errors"""

    pass


class StripeService:
    """
    Service class to handle Stripe Checkout, webhook operations, and payment polling
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

    def poll_payment_status(
        self, payment_id: int, max_attempts: int = 5
    ) -> Dict[str, Any]:
        """
        Poll payment status from Stripe - intended for admin use when webhooks fail
        """
        from apps.Job.models import Job
        from apps.Request.models import Request  # Add Request model import

        try:
            print(f"\nStarting poll_payment_status for payment {payment_id}")
            payment = Payment.objects.select_related("request").get(
                id=payment_id
            )  # Use select_related to get request in same query
            original_status = payment.status
            print(f"Found payment with original status: {original_status}")

            # Try to get current status from Stripe
            stripe_data = self._get_stripe_payment_status(payment)
            print(f"Got stripe data: {stripe_data}")

            if not stripe_data:
                print("Could not retrieve payment status from Stripe")
                return {
                    "success": False,
                    "error": "Could not retrieve payment status from Stripe",
                    "payment_id": payment_id,
                    "current_status": payment.status,
                }

            # Update local payment record based on Stripe data
            try:
                updated_payment = self._update_payment_from_stripe_data(
                    payment, stripe_data
                )
                print(f"Updated payment status: {updated_payment.status}")

                if updated_payment.status == "completed":
                    print("Payment completed, updating request and creating job")
                    if updated_payment.request:  # Check if request exists
                        print(f"Updating request {updated_payment.request.id} status")
                        updated_payment.request.payment_status = "completed"
                        updated_payment.request.save()
                        try:
                            # Create job after payment
                            job = Job.create_job_after_payment(updated_payment.request)
                            print(f"Successfully created job {job.id}")
                        except Exception as e:
                            print(f"Error creating job: {str(e)}")
                            # Don't fail the whole process if job creation fails
                            logger.error(
                                f"Failed to create job for request {updated_payment.request.id}: {str(e)}"
                            )

                return {
                    "success": True,
                    "payment_id": payment_id,
                    "original_status": original_status,
                    "current_status": updated_payment.status,
                    "stripe_status": stripe_data.get("status"),
                    "payment_intent_id": stripe_data.get("payment_intent_id"),
                    "amount": str(updated_payment.amount),
                    "currency": updated_payment.currency,
                    "last_updated": (
                        updated_payment.updated_at.isoformat()
                        if updated_payment.updated_at
                        else None
                    ),
                    "changes_made": original_status != updated_payment.status,
                    "stripe_data": stripe_data,
                }
            except Exception as e:
                print(f"Error updating payment from stripe data: {str(e)}")
                return {"success": False, "error": str(e), "payment_id": payment_id}

        except Payment.DoesNotExist:
            print(f"Payment with ID {payment_id} not found")
            return {
                "success": False,
                "error": f"Payment with ID {payment_id} not found",
                "payment_id": payment_id,
            }
        except Exception as e:
            print(f"Error polling payment status: {str(e)}")
            logger.error(
                f"Error polling payment status for payment {payment_id}: {str(e)}"
            )
            return {"success": False, "error": str(e), "payment_id": payment_id}

    def poll_payment_until_complete(
        self, payment_id: int, max_attempts: int = 10, base_delay: float = 2.0
    ) -> Dict[str, Any]:
        """
        Poll payment status until it reaches a terminal state (completed, failed, refunded, etc.)

        Args:
            payment_id: Local Payment model ID
            max_attempts: Maximum polling attempts
            base_delay: Base delay in seconds (will use exponential backoff)

        Returns:
            Dict with final status and polling results
        """
        payment = Payment.objects.get(id=payment_id)
        original_status = payment.status
        attempts = 0

        # Terminal states where we stop polling
        terminal_states = [
            "completed",
            "failed",
            "refunded",
            "partially_refunded",
            "canceled",
        ]

        logger.info(
            f"Starting polling for payment {payment_id}, current status: {payment.status}"
        )

        while attempts < max_attempts:
            attempts += 1

            try:
                # Poll current status
                result = self.poll_payment_status(payment_id, max_attempts=1)

                if not result["success"]:
                    logger.warning(
                        f"Polling attempt {attempts} failed for payment {payment_id}: {result.get('error')}"
                    )
                    if attempts == max_attempts:
                        return {
                            "success": False,
                            "error": f"All {max_attempts} polling attempts failed",
                            "payment_id": payment_id,
                            "final_status": payment.status,
                            "attempts": attempts,
                        }
                    continue

                # Check if we've reached a terminal state
                current_status = result["current_status"]
                if current_status in terminal_states:
                    logger.info(
                        f"Payment {payment_id} reached terminal state: {current_status}"
                    )
                    return {
                        "success": True,
                        "payment_id": payment_id,
                        "original_status": original_status,
                        "final_status": current_status,
                        "attempts": attempts,
                        "terminal_state_reached": True,
                        "stripe_data": result.get("stripe_data", {}),
                    }

                # If not terminal and not last attempt, wait before next poll
                if attempts < max_attempts:
                    delay = base_delay * (2 ** (attempts - 1))  # Exponential backoff
                    logger.debug(
                        f"Payment {payment_id} still pending, waiting {delay}s before next poll"
                    )
                    time.sleep(delay)

            except Exception as e:
                logger.error(
                    f"Error in polling attempt {attempts} for payment {payment_id}: {str(e)}"
                )
                if attempts == max_attempts:
                    return {
                        "success": False,
                        "error": f"Polling failed after {attempts} attempts: {str(e)}",
                        "payment_id": payment_id,
                        "final_status": payment.status,
                        "attempts": attempts,
                    }

        # Max attempts reached without terminal state
        return {
            "success": True,
            "payment_id": payment_id,
            "original_status": original_status,
            "final_status": payment.status,
            "attempts": attempts,
            "terminal_state_reached": False,
            "message": f"Polling completed after {attempts} attempts, payment still in non-terminal state",
        }

    def _get_stripe_payment_status(self, payment: Payment) -> Optional[Dict[str, Any]]:
        """
        Get current payment status from Stripe based on available identifiers
        """
        try:
            print(f"Getting stripe payment status for payment {payment.id}")
            print(f"Payment intent ID: {payment.stripe_payment_intent_id}")
            print(f"Transaction ID: {payment.transaction_id}")

            # Try payment intent first (if available)
            if payment.stripe_payment_intent_id:
                print("Using payment intent ID")
                return self._get_payment_intent_status(payment.stripe_payment_intent_id)

            # Fall back to checkout session (transaction_id)
            elif payment.transaction_id and payment.transaction_id.startswith("cs_"):
                print("Using checkout session ID")
                return self._get_checkout_session_status(payment.transaction_id)

            else:
                print(f"Payment {payment.id} has no valid Stripe identifier")
                logger.error(f"Payment {payment.id} has no valid Stripe identifier")
                return None

        except stripe.error.StripeError as e:
            print(f"Stripe error when getting payment status: {str(e)}")
            logger.error(f"Stripe error when getting payment status: {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected error in _get_stripe_payment_status: {str(e)}")
            logger.error(f"Unexpected error in _get_stripe_payment_status: {str(e)}")
            return None

    def _get_payment_intent_status(self, payment_intent_id: str) -> Dict[str, Any]:
        """Get status from payment intent"""
        try:
            print(f"Getting payment intent status for {payment_intent_id}")
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            print(f"Payment intent retrieved: {payment_intent}")

            # Safely get charges data
            charges_data = []
            if hasattr(payment_intent, "charges") and payment_intent.charges:
                charges_data = (
                    payment_intent.charges.data
                    if hasattr(payment_intent.charges, "data")
                    else []
                )

            return {
                "source": "payment_intent",
                "payment_intent_id": payment_intent.id,
                "status": payment_intent.status,
                "amount": Decimal(payment_intent.amount) / 100,
                "currency": payment_intent.currency.upper(),
                "last_payment_error": payment_intent.last_payment_error,
                "charges": charges_data,
            }
        except Exception as e:
            print(f"Error in _get_payment_intent_status: {str(e)}")
            raise

    def _get_checkout_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get status from checkout session"""
        session = stripe.checkout.Session.retrieve(session_id)
        result = {
            "source": "checkout_session",
            "session_id": session.id,
            "payment_status": session.payment_status,
            "status": session.status,
            "amount": (
                Decimal(session.amount_total) / 100 if session.amount_total else None
            ),
            "currency": session.currency.upper() if session.currency else None,
            "payment_intent_id": session.payment_intent,
        }

        # If session has payment intent, get additional details
        if session.payment_intent:
            try:
                payment_intent = stripe.PaymentIntent.retrieve(session.payment_intent)
                result.update(
                    {
                        "payment_intent_status": payment_intent.status,
                        "last_payment_error": payment_intent.last_payment_error,
                    }
                )
            except stripe.error.StripeError as e:
                logger.warning(
                    f"Could not retrieve payment intent {session.payment_intent}: {str(e)}"
                )

        return result

    def _update_payment_from_stripe_data(
        self, payment: Payment, stripe_data: Dict[str, Any]
    ) -> Payment:
        """
        Update local payment record based on Stripe data
        """
        with transaction.atomic():
            payment.refresh_from_db()

            # Determine new status based on Stripe data
            new_status = self._map_stripe_status_to_local(stripe_data)

            # Update payment intent ID if we got it from checkout session
            if not payment.stripe_payment_intent_id and stripe_data.get(
                "payment_intent_id"
            ):
                payment.stripe_payment_intent_id = stripe_data["payment_intent_id"]

            # Update status and related fields
            if new_status != payment.status:
                old_status = payment.status
                payment.status = new_status

                # Set completion/failure timestamps
                if new_status == "completed" and not payment.completed_at:
                    payment.completed_at = timezone.now()
                    payment.request.payment_status = "completed"
                elif new_status == "failed" and not payment.failed_at:
                    payment.failed_at = timezone.now()
                    if stripe_data.get("last_payment_error"):
                        payment.failure_reason = stripe_data["last_payment_error"].get(
                            "message", "Payment failed"
                        )
                elif (
                    new_status in ["refunded", "partially_refunded"]
                    and not payment.refunded_at
                ):
                    payment.refunded_at = timezone.now()

                # Update request status if payment completed
                if (
                    new_status == "completed"
                    and payment.request
                    and payment.request.status != "confirmed"
                ):
                    payment.request.status = "confirmed"
                    payment.request.save()
                    logger.info(
                        f"Updated request {payment.request.id} status to confirmed after payment completion"
                    )

                logger.info(
                    f"Updated payment {payment.id} status from {old_status} to {new_status}"
                )

            payment.save()
            return payment

    def _map_stripe_status_to_local(self, stripe_data: Dict[str, Any]) -> str:
        """
        Map Stripe payment status to local payment status
        """
        source = stripe_data.get("source")

        if source == "checkout_session":
            payment_status = stripe_data.get("payment_status")
            if payment_status == "paid":
                return "completed"
            elif payment_status == "unpaid":
                return "pending"
            elif payment_status == "no_payment_required":
                return "completed"

        elif source == "payment_intent":
            intent_status = stripe_data.get("status")
            if intent_status == "succeeded":
                return "completed"
            elif intent_status in ["requires_payment_method", "canceled"]:
                return "failed"
            elif intent_status in [
                "requires_confirmation",
                "requires_action",
                "processing",
            ]:
                return "pending"

        # Check for refunds in charges
        charges = stripe_data.get("charges", [])
        for charge in charges:
            if charge.get("refunded"):
                amount_refunded = charge.get("amount_refunded", 0)
                total_amount = charge.get("amount", 0)
                if amount_refunded >= total_amount:
                    return "refunded"
                elif amount_refunded > 0:
                    return "partially_refunded"

        # Default to current status if unclear
        return "pending"

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
                "url": getattr(session, "url", None),
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

    def expire_checkout_session(self, session_id: str) -> bool:
        """
        Expire an open checkout session to prevent further use.

        Returns True if expired (or already non-open), False otherwise.
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            # Only expire if session is open
            if getattr(session, "status", None) == "open":
                stripe.checkout.Session.expire(session_id)
                logger.info(f"Expired checkout session {session_id}")
            else:
                logger.info(
                    f"Checkout session {session_id} not open (status={session.status}), skipping expire"
                )
            return True
        except stripe.error.StripeError as e:
            logger.error(f"Error expiring checkout session {session_id}: {str(e)}")
            return False

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
