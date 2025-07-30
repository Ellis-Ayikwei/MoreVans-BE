# OTP API Documentation

## Overview
This document describes the new clean OTP implementation using django-otp. The system provides three main authentication flows:

1. **Normal Login**: Standard email/password authentication
2. **MFA Login**: Two-step email/password + OTP authentication
3. **TOTP MFA**: Email/password + TOTP (Time-based One-Time Password) authentication

## API Endpoints

### 1. Send OTP
**POST** `/api/auth/otp/send/`

Send OTP to user's email for various purposes.

**Request Body:**
```json
{
    "email": "user@example.com",
    "otp_type": "signup" | "login" | "password_reset" | "email_change"
}
```

**Response:**
```json
{
    "message": "OTP sent successfully to j***@example.com",
    "masked_email": "j***@example.com",
    "validity_minutes": 10,
    "otp_type": "signup"
}
```

### 2. Verify OTP
**POST** `/api/auth/otp/verify/`

Verify OTP and perform action based on type.

**Request Body:**
```json
{
    "email": "user@example.com",
    "otp_code": "123456",
    "otp_type": "signup" | "login" | "password_reset" | "email_change"
}
```

**Response for Signup:**
```json
{
    "message": "Email verified successfully. Your account is now active.",
    "action": "account_activated",
    "user_id": "123"
}
```

**Response for Login:**
```json
{
    "message": "OTP verified successfully for login.",
    "action": "login_verified",
    "user_id": "123",
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 123,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "is_active": true
    }
}
```

### 3. MFA Login (Step 1)
**POST** `/api/auth/mfa/login/`

Authenticate with email/password and send OTP for MFA.

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "userpassword"
}
```

**Response:**
```json
{
    "message": "Password verified. Please check your email for OTP to complete login.",
    "masked_email": "j***@example.com",
    "user_id": "123",
    "otp_sent": true,
    "mfa_required": true,
    "validity_minutes": 10
}
```

### 4. MFA Login (Step 2)
**POST** `/api/auth/mfa/verify/`

Verify OTP and complete MFA login.

**Request Body:**
```json
{
    "email": "user@example.com",
    "otp_code": "123456"
}
```

**Response:**
```json
{
    "message": "MFA login successful.",
    "action": "mfa_login_completed",
    "user_id": "123",
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 123,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "is_active": true
    }
}
```

### 5. Resend OTP
**POST** `/api/auth/otp/resend/`

Resend OTP to user's email.

**Request Body:**
```json
{
    "email": "user@example.com",
    "otp_type": "signup" | "login" | "password_reset" | "email_change"
}
```

### 6. TOTP MFA Verification
**POST** `/api/auth/mfa/totp/`

Verify TOTP during MFA login.

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "userpassword",
    "totp_code": "123456"
}
```

**Response:**
```json
{
    "message": "MFA verification successful.",
    "action": "mfa_verified",
    "user_id": "123",
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 123,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "is_active": true
    }
}
```

## Authentication Flows

### 1. User Registration Flow
1. User registers with email/password
2. System automatically sends OTP to email
3. User verifies OTP to activate account
4. Account becomes active

### 2. Normal Login Flow
1. User provides email/password
2. System validates credentials
3. Returns JWT tokens
4. User is authenticated

### 3. MFA Login Flow (Two-Step)
1. **Step 1**: User provides email/password
2. System validates credentials and sends OTP to email
3. **Step 2**: User provides OTP code
4. System verifies OTP and returns JWT tokens
5. User is authenticated

### 4. TOTP MFA Flow
1. User provides email/password + TOTP code
2. System validates all credentials
3. Returns JWT tokens
4. User is authenticated

### 5. Password Reset Flow
1. User requests password reset
2. System sends OTP to email
3. User verifies OTP
4. User can set new password

## Error Codes

- `USER_NOT_FOUND`: User with email not found
- `INVALID_CREDENTIALS`: Invalid email or password
- `ACCOUNT_INACTIVE`: Account is not active
- `RATE_LIMIT_EXCEEDED`: Too many OTP requests
- `COOLDOWN_ACTIVE`: Please wait before requesting another OTP
- `DEVICE_NOT_FOUND`: No OTP device found for user
- `INVALID_OTP`: Invalid OTP code
- `VERIFICATION_FAILED`: Failed to verify OTP
- `INTERNAL_ERROR`: Internal server error

## Rate Limiting

- **OTP Requests**: Max 5 requests per hour per user
- **Cooldown**: 1 minute between OTP requests
- **OTP Validity**: 10 minutes

## Security Features

- Email masking for privacy
- Rate limiting to prevent abuse
- Automatic device cleanup
- Secure token generation
- Audit logging

## Frontend Integration Example

### MFA Login Flow
```javascript
// Step 1: Send email/password and get OTP
const mfaLoginResponse = await fetch('/api/auth/mfa/login/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        email: 'user@example.com',
        password: 'userpassword'
    })
});

if (mfaLoginResponse.ok) {
    const data = await mfaLoginResponse.json();
    // Show OTP input form
    // data.masked_email contains masked email for display
}

// Step 2: Verify OTP and get tokens
const verifyMfaResponse = await fetch('/api/auth/mfa/verify/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        email: 'user@example.com',
        otp_code: '123456'
    })
});

if (verifyMfaResponse.ok) {
    const data = await verifyMfaResponse.json();
    // Store tokens
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    // Redirect to dashboard
}
```

## Migration from Legacy OTP

The old OTP endpoints are still available under `/api/auth/legacy/` for backward compatibility but are deprecated and will be removed in future versions.

**Legacy Endpoints:**
- `/api/auth/legacy/otp/send/`
- `/api/auth/legacy/otp/verify/`
- `/api/auth/legacy/otp/resend/`
- `/api/auth/legacy/login/otp/`