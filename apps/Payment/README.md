# MoreVans Payment Integration with Stripe Checkout

This document explains how to use the Stripe Checkout integration for the MoreVans platform.

## Overview

The payment system uses **Stripe Checkout** - a pre-built payment page hosted by Stripe. This approach provides:

- PCI compliance without additional certification
- Built-in fraud protection
- Mobile-optimized payment forms
- Multiple payment methods support
- Automatic webhooks for payment status updates

## Environment Variables

Add these to your environment variables or `.env` file:

```bash
# Stripe Keys (get from Stripe Dashboard)
STRIPE_PUBLISHABLE_KEY=pk_test_... # Your test publishable key
STRIPE_SECRET_KEY=sk_test_...      # Your test secret key
STRIPE_WEBHOOK_SECRET=whsec_...    # Your webhook endpoint secret

# URLs for redirects
PAYMENT_SUCCESS_URL=http://localhost:3000/payment/success
PAYMENT_CANCEL_URL=http://localhost:3000/payment/cancel
```

## API Endpoints

### 1. Get Stripe Configuration

Get the publishable key and configuration for frontend.

```http
GET /api/payments/config/
Authorization: Bearer <token>
```

**Response:**

```json
{
  "publishable_key": "pk_test_...",
  "currency": "usd",
  "supported_currencies": ["usd", "eur", "gbp", "ghs"],
  "success_url": "http://localhost:3000/payment/success",
  "cancel_url": "http://localhost:3000/payment/cancel"
}
```

### 2. Create Checkout Session

Create a Stripe Checkout session for payment.

```http
POST /api/payments/payments/create_checkout_session/
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**

```json
{
  "request_id": "uuid-of-the-request",
  "amount": 150.0,
  "currency": "USD",
  "success_url": "http://localhost:3000/payment/success?session_id={CHECKOUT_SESSION_ID}",
  "cancel_url": "http://localhost:3000/payment/cancel",
  "description": "Moving service payment"
}
```

**Response:**

```json
{
  "id": "cs_test_...",
  "url": "https://checkout.stripe.com/c/pay/cs_test_...",
  "status": "open",
  "amount": 150.0,
  "currency": "USD"
}
```

### 3. Check Session Status

Check the status of a checkout session.

```http
GET /api/payments/payments/check_session_status/?session_id=cs_test_...
Authorization: Bearer <token>
```

**Response:**

```json
{
  "id": "cs_test_...",
  "status": "complete",
  "payment_status": "paid",
  "amount_total": 150.0,
  "currency": "usd",
  "customer_email": "user@example.com",
  "metadata": {
    "user_id": "123",
    "request_id": "456",
    "platform": "morevans"
  },
  "payment_intent": "pi_..."
}
```

### 4. Create Refund

Create a refund for a completed payment.

```http
POST /api/payments/payments/create_refund/
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**

```json
{
  "payment_intent_id": "pi_...",
  "amount": 50.0, // Optional: partial refund
  "reason": "Customer requested cancellation"
}
```

### 5. List Payments

List payments for the authenticated user.

```http
GET /api/payments/payments/
Authorization: Bearer <token>
```

Query parameters:

- `request`: Filter by request ID
- `status`: Filter by payment status

### 6. Webhook Endpoint

Stripe will send webhook events to this endpoint.

```http
POST /api/payments/webhook/
Content-Type: application/json
Stripe-Signature: t=...,v1=...
```

## Frontend Integration

### 1. Get Configuration

```javascript
const response = await fetch("/api/payments/config/", {
  headers: {
    Authorization: `Bearer ${token}`,
  },
});
const config = await response.json();
```

### 2. Create Checkout Session

```javascript
const response = await fetch(
  "/api/payments/payments/create_checkout_session/",
  {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      request_id: requestId,
      amount: 150.0,
      currency: "USD",
      success_url: `${window.location.origin}/payment/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${window.location.origin}/payment/cancel`,
      description: "Moving service payment",
    }),
  }
);

const session = await response.json();

// Redirect to Stripe Checkout
window.location.href = session.url;
```

### 3. Handle Success Page

```javascript
// On success page, extract session_id from URL
const urlParams = new URLSearchParams(window.location.search);
const sessionId = urlParams.get("session_id");

// Check payment status
const response = await fetch(
  `/api/payments/payments/check_session_status/?session_id=${sessionId}`,
  {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  }
);
const sessionStatus = await response.json();

if (sessionStatus.payment_status === "paid") {
  // Payment successful!
}
```

## Webhook Events

The following Stripe webhook events are handled:

### 1. checkout.session.completed

Triggered when a checkout session is completed successfully.

- Updates payment status to 'completed'
- Updates request status to 'confirmed'
- Can trigger job creation or other business logic

### 2. payment_intent.succeeded

Backup event for payment success.

### 3. payment_intent.payment_failed

Triggered when a payment fails.

- Updates payment status to 'failed'
- Records failure reason

### 4. charge.refunded

Triggered when a refund is processed.

- Updates payment status to 'refunded' or 'partially_refunded'

### 5. charge.dispute.created

Triggered when a chargeback/dispute is created.

- Adds dispute metadata to payment record

## Database Models

### Payment

- `request`: ForeignKey to Request
- `amount`: Payment amount
- `currency`: Currency code (USD, EUR, etc.)
- `status`: Payment status (pending, completed, failed, etc.)
- `transaction_id`: Stripe checkout session ID
- `stripe_payment_intent_id`: Stripe payment intent ID (set after completion)
- `description`: Payment description
- `metadata`: Additional data from Stripe

### StripeEvent

- `stripe_event_id`: Unique Stripe event ID
- `event_type`: Type of event (checkout.session.completed, etc.)
- `processed`: Whether the event has been processed
- Prevents duplicate processing of webhook events

## Testing

### 1. Use Stripe Test Mode

Make sure you're using test keys (`pk_test_...` and `sk_test_...`).

### 2. Test Card Numbers

Use Stripe's test card numbers:

- Successful payment: `4242424242424242`
- Declined payment: `4000000000000002`
- Authentication required: `4000002500003155`

### 3. Webhook Testing

Use Stripe CLI to forward webhooks to local development:

```bash
stripe listen --forward-to localhost:8000/api/payments/webhook/
```

## Security

1. **Webhook Verification**: All webhook events are verified using Stripe's signature
2. **Event Deduplication**: Events are stored to prevent duplicate processing
3. **User Authorization**: All API endpoints require authentication
4. **Amount Validation**: Payment amounts are validated on both frontend and backend

## Production Checklist

1. ✅ Replace test keys with live Stripe keys
2. ✅ Set up proper webhook endpoint with HTTPS
3. ✅ Configure proper success/cancel URLs
4. ✅ Test webhook delivery in production
5. ✅ Set up monitoring for failed payments
6. ✅ Configure email notifications for payment events
