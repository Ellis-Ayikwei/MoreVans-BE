# OTP System API Documentation

## Overview

The OTP (One-Time Password) system provides secure user authentication and verification through email-based OTP codes. It supports user sign-up verification, login authentication, password reset, and other verification scenarios.

## Features

- **Email-based OTP delivery** with beautiful HTML templates
- **Multiple OTP types**: signup, login, password reset, email change, phone change
- **Security features**: rate limiting, attempt tracking, expiration, masking
- **User verification tracking**: email and phone verification status
- **Flexible OTP validity periods** and customizable attempt limits

## API Endpoints

### 1. User Registration

**Endpoint**: `POST /api/auth/register/`

**Description**: Register a new user account. The user will be created as inactive and an OTP will be sent for email verification.

**Request Body**:
```json
{
    "email": "user@example.com",
    "password": "SecurePassword123",
    "password2": "SecurePassword123"
}
```

**Response**:
```json
{
    "message": "User created successfully. Please check your email for verification code.",
    "email": "u***@example.com",
    "user_id": "uuid-here",
    "otp_sent": true
}
```

### 2. Send OTP

**Endpoint**: `POST /api/auth/otp/send/`

**Description**: Send an OTP to user's email for various purposes.

**Request Body**:
```json
{
    "email": "user@example.com",
    "otp_type": "signup"  // Options: signup, login, password_reset, email_change, phone_change
}
```

**Response**:
```json
{
    "message": "OTP sent successfully to u***@example.com",
    "masked_recipient": "u***@example.com",
    "validity_minutes": 10
}
```

### 3. Verify OTP

**Endpoint**: `POST /api/auth/otp/verify/`

**Description**: Verify an OTP code and perform the associated action.

**Request Body**:
```json
{
    "email": "user@example.com",
    "otp_code": "123456",
    "otp_type": "signup"
}
```

**Response (for signup)**:
```json
{
    "message": "Email verified successfully. Your account is now active.",
    "refresh": "jwt-refresh-token",
    "access": "jwt-access-token",
    "user": {
        "id": "uuid",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe"
    }
}
```

### 4. Resend OTP

**Endpoint**: `POST /api/auth/otp/resend/`

**Description**: Resend an OTP (with rate limiting).

**Request Body**:
```json
{
    "email": "user@example.com",
    "otp_type": "signup"
}
```

**Response**: Same as Send OTP endpoint

### 5. Login with OTP

**Endpoint**: `POST /api/auth/login/otp/`

**Description**: Login using OTP instead of password.

**Request Body (Request OTP)**:
```json
{
    "email": "user@example.com",
    "request_otp": true
}
```

**Response**:
```json
{
    "message": "OTP sent to u***@example.com",
    "masked_email": "u***@example.com",
    "otp_required": true
}
```

**Request Body (Verify OTP)**:
```json
{
    "email": "user@example.com",
    "otp_code": "123456"
}
```

**Response**:
```json
{
    "message": "Login successful",
    "refresh": "jwt-refresh-token",
    "access": "jwt-access-token",
    "user": {
        "id": "uuid",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe"
    }
}
```

## Error Responses

### Rate Limiting Error
```json
{
    "detail": "Too many OTP requests. Please try again later."
}
```
**Status Code**: 429

### Invalid OTP
```json
{
    "detail": "Invalid OTP. 2 attempts remaining."
}
```
**Status Code**: 400

### Expired OTP
```json
{
    "detail": "Invalid or expired OTP."
}
```
**Status Code**: 400

## Security Features

1. **Rate Limiting**:
   - Maximum 5 OTP requests per hour per user
   - 1-minute cooldown between OTP resends

2. **OTP Security**:
   - 6-digit numeric codes
   - 10-minute validity period (configurable)
   - Maximum 3 verification attempts per OTP
   - Automatic invalidation of previous unused OTPs

3. **Email Masking**:
   - Emails are masked in responses (e.g., `j***@example.com`)
   - Prevents email enumeration attacks

## Email Templates

The system uses responsive HTML email templates with:
- Professional design with green theme
- Clear OTP display with large, readable font
- Security warnings
- Mobile-responsive layout
- Plain text fallback

## Database Models

### OTP Model
```python
- user: ForeignKey to User
- otp_code: 6-digit code
- otp_type: Type of OTP (signup, login, etc.)
- is_used: Boolean flag
- created_at: Timestamp
- expires_at: Expiration timestamp
- attempts: Number of verification attempts
- max_attempts: Maximum allowed attempts (default: 3)
```

### UserVerification Model
```python
- user: OneToOneField to User
- email_verified: Boolean
- phone_verified: Boolean
- email_verified_at: Timestamp
- phone_verified_at: Timestamp
```

## Integration Example

### Frontend Integration (JavaScript)

```javascript
// Register new user
async function register(email, password) {
    const response = await fetch('/api/auth/register/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            email: email,
            password: password,
            password2: password
        })
    });
    
    if (response.ok) {
        const data = await response.json();
        // Redirect to OTP verification page
        window.location.href = `/verify-otp?email=${email}&type=signup`;
    }
}

// Verify OTP
async function verifyOTP(email, otpCode, otpType) {
    const response = await fetch('/api/auth/otp/verify/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            email: email,
            otp_code: otpCode,
            otp_type: otpType
        })
    });
    
    if (response.ok) {
        const data = await response.json();
        // Store tokens
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        // Redirect to dashboard
        window.location.href = '/dashboard';
    }
}
```

## Testing

Run the test script to verify the OTP system:

```bash
python test_otp_system.py
```

This will:
1. Create a test user
2. Generate and verify OTPs
3. Test email template rendering
4. Demonstrate the complete OTP flow

## Migration

Apply the OTP models migration:

```bash
python manage.py migrate Authentication
```

## Environment Variables

Ensure these email settings are configured in your `.env` file:

```env
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
```