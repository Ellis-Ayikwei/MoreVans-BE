# OTP (One-Time Password) System Documentation

## Overview

This document describes the comprehensive OTP (One-Time Password) system implemented for user authentication, signup verification, and enhanced security features in the MoreVans application.

## Features

### 🔐 Security Features
- **6-digit numeric OTP codes** with 10-minute expiration
- **Rate limiting** to prevent abuse (5 attempts per 15 minutes)
- **IP-based tracking** for suspicious activity detection
- **Automatic cleanup** of expired OTP records
- **Secure email templates** with HTML and plain text versions

### 📧 Email Integration
- **Beautiful HTML email templates** with responsive design
- **Professional branding** with MoreVans styling
- **Multiple OTP types** with context-aware messaging
- **Fallback plain text** for email clients that don't support HTML

### 🚀 Multiple OTP Types
- `signup_verification` - New user account verification
- `login_verification` - Enhanced login security (2FA)
- `password_reset` - Secure password reset flow
- `email_change` - Email address change verification

### 📊 Admin Interface
- **Django admin integration** with custom admin classes
- **Read-only login attempt tracking**
- **OTP management** with security restrictions
- **Statistics and monitoring** capabilities

## API Endpoints

### 1. Request OTP
**POST** `/auth/otp/request/`

Request a new OTP for various purposes.

```json
{
    "email": "user@example.com",
    "otp_type": "signup_verification"
}
```

**Response:**
```json
{
    "message": "Verification code sent to user@example.com",
    "expires_in": 600,
    "remaining_attempts": 4
}
```

### 2. Verify OTP
**POST** `/auth/otp/verify/`

Verify an OTP code.

```json
{
    "email": "user@example.com",
    "otp_code": "123456",
    "otp_type": "signup_verification"
}
```

**Response:**
```json
{
    "message": "Verification successful",
    "verified": true,
    "next_step": "complete_registration"
}
```

### 3. Enhanced Registration
**POST** `/auth/register-otp/`

Register with OTP verification.

```json
{
    "email": "user@example.com",
    "password": "securepassword123",
    "password2": "securepassword123",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890",
    "user_type": "customer",
    "otp_code": "123456"
}
```

**Response:**
```json
{
    "message": "Account created and verified successfully!",
    "user_id": "uuid-string",
    "email": "user@example.com"
}
```

### 4. Enhanced Login
**POST** `/auth/login-otp/`

Login with optional OTP verification.

```json
{
    "email": "user@example.com",
    "password": "securepassword123",
    "otp_code": "123456",
    "remember_me": false
}
```

**Response (when OTP required):**
```json
{
    "detail": "Verification code required",
    "requires_otp": true,
    "message": "Verification code sent to user@example.com"
}
```

**Response (successful login):**
```json
{
    "access_token": "jwt-token",
    "refresh_token": "refresh-token",
    "user": { /* user data */ },
    "message": "Login successful"
}
```

## Database Models

### OTP Model
```python
class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=6)
    otp_type = models.CharField(max_length=20, choices=OTP_TYPES)
    email = models.EmailField()
    is_used = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
```

### LoginAttempt Model
```python
class LoginAttempt(models.Model):
    email = models.EmailField()
    ip_address = models.GenericIPAddressField()
    attempt_time = models.DateTimeField(auto_now_add=True)
    is_successful = models.BooleanField(default=False)
```

## Service Class

### OTPService Methods

#### `generate_otp(user, otp_type, email=None)`
Generates and saves a new OTP for a user.

#### `verify_otp(code, otp_type, email, user=None)`
Verifies an OTP code and returns validation result.

#### `send_otp_email(otp, request=None)`
Sends OTP via email using HTML/text templates.

#### `check_rate_limit(email, ip_address, max_attempts=5, window_minutes=15)`
Checks if user has exceeded rate limits.

#### `cleanup_expired_otps()`
Removes expired OTP records from database.

## Email Templates

### HTML Template (`otp_verification.html`)
- **Professional design** with gradient styling
- **Responsive layout** for mobile devices
- **Security warnings** and contact information
- **Context-aware messaging** based on OTP type

### Text Template (`otp_verification.txt`)
- **Plain text fallback** for all email clients
- **Consistent formatting** with HTML version
- **All essential information** preserved

## Configuration

### Settings Requirements
```python
# Email Configuration
EMAIL_BACKEND = "apps.Authentication.email_backend.GmailSSLBackend"
DEFAULT_FROM_EMAIL = "noreply@morevans.com"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 465
EMAIL_HOST_USER = "your-email@gmail.com"
EMAIL_HOST_PASSWORD = "your-app-password"
EMAIL_USE_TLS = True

# Template Directories
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "apps", "Authentication", "templates"),
            # ... other template dirs
        ],
        # ...
    },
]
```

### Environment Variables
```bash
DEFAULT_FROM_EMAIL=noreply@morevans.com
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=465
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
```

## Security Considerations

### Rate Limiting
- **5 OTP requests per 15 minutes** per email
- **10 OTP requests per 15 minutes** per IP address
- **Exponential backoff** for repeated violations

### OTP Security
- **6-digit numeric codes** (easy to type, secure enough)
- **10-minute expiration** (balance between security and usability)
- **Single-use only** (automatically invalidated after verification)
- **Case-insensitive verification**

### Login Security
- **Failed attempt tracking** with temporary lockouts
- **IP address monitoring** for suspicious activity
- **Admin user automatic 2FA** requirement
- **Risk-based authentication** triggers

## Management Commands

### Cleanup Expired OTPs
```bash
python manage.py cleanup_expired_otps
```

Options:
- `--days=7`: Number of days to keep login attempts (default: 7)
- `--dry-run`: Show what would be deleted without deleting

Example:
```bash
python manage.py cleanup_expired_otps --days=3 --dry-run
```

## Frontend Integration Examples

### JavaScript/React Example
```javascript
// Request OTP
const requestOTP = async (email, otpType) => {
    const response = await fetch('/auth/otp/request/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            email: email,
            otp_type: otpType
        })
    });
    return await response.json();
};

// Verify OTP
const verifyOTP = async (email, code, otpType) => {
    const response = await fetch('/auth/otp/verify/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            email: email,
            otp_code: code,
            otp_type: otpType
        })
    });
    return await response.json();
};

// Enhanced Registration Flow
const registerWithOTP = async (userData) => {
    // 1. Request OTP first
    await requestOTP(userData.email, 'signup_verification');
    
    // 2. Show OTP input to user
    const otpCode = await getUserOTPInput();
    
    // 3. Register with OTP
    const response = await fetch('/auth/register-otp/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            ...userData,
            otp_code: otpCode
        })
    });
    return await response.json();
};
```

## Error Handling

### Common Error Responses

#### Rate Limit Exceeded
```json
{
    "detail": "Too many verification requests. Please wait 15 minutes before trying again.",
    "status": 429
}
```

#### Invalid OTP
```json
{
    "detail": "Invalid or expired verification code",
    "verified": false,
    "status": 400
}
```

#### Email Not Found
```json
{
    "message": "If an account exists with this email, a verification code has been sent.",
    "status": 200
}
```

## Testing

### Unit Tests
```python
from django.test import TestCase
from apps.Authentication.otp_service import OTPService
from apps.User.models import User

class OTPServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_generate_otp(self):
        otp = OTPService.generate_otp(
            self.user, 
            'signup_verification'
        )
        self.assertEqual(len(otp.code), 6)
        self.assertTrue(otp.code.isdigit())
    
    def test_verify_otp(self):
        otp = OTPService.generate_otp(
            self.user, 
            'signup_verification'
        )
        result = OTPService.verify_otp(
            otp.code,
            'signup_verification',
            self.user.email
        )
        self.assertTrue(result['success'])
```

## Monitoring and Analytics

### Key Metrics to Track
- **OTP success rate** (verification success vs. total requests)
- **Email delivery rate** (sent vs. failed emails)
- **User completion rate** (started vs. completed flows)
- **Security incidents** (rate limit violations, suspicious patterns)

### Logging
The system includes comprehensive logging:
- **OTP generation** with user and type information
- **Verification attempts** (success and failure)
- **Rate limit violations** with IP tracking
- **Email sending status** (success/failure)

## Troubleshooting

### Common Issues

#### OTP Email Not Received
1. Check spam/junk folder
2. Verify email configuration in settings
3. Check email provider settings (app passwords for Gmail)
4. Review email backend logs

#### Database Connection Issues
1. Ensure PostgreSQL is running
2. Check database credentials in settings
3. Verify database migrations are applied

#### Template Not Found Errors
1. Check `TEMPLATES['DIRS']` includes Authentication templates
2. Verify template files exist in correct directories
3. Ensure file permissions are correct

### Debug Commands
```bash
# Check email configuration
python manage.py shell -c "from django.core.mail import send_mail; send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])"

# Test OTP generation
python manage.py shell -c "from apps.Authentication.otp_service import OTPService; from apps.User.models import User; user = User.objects.first(); otp = OTPService.generate_otp(user, 'signup_verification'); print(f'Generated OTP: {otp.code}')"

# Cleanup expired OTPs (dry run)
python manage.py cleanup_expired_otps --dry-run
```

## Future Enhancements

### Planned Features
- **SMS OTP support** for phone verification
- **Time-based OTP (TOTP)** for authenticator apps
- **Backup codes** for account recovery
- **Biometric verification** integration
- **Advanced fraud detection** with machine learning
- **Multi-channel delivery** (email + SMS + push notifications)

### Performance Optimizations
- **Redis caching** for rate limiting
- **Async email sending** with Celery
- **Database query optimization** with select_related
- **CDN integration** for email assets

---

## Support

For questions or issues related to the OTP system:

1. **Documentation**: Refer to this document
2. **Code Review**: Check the implementation in `apps/Authentication/`
3. **Testing**: Run the test suite to verify functionality
4. **Monitoring**: Check Django admin for OTP and login attempt records

**Author**: MoreVans Development Team  
**Last Updated**: 2024  
**Version**: 1.0.0