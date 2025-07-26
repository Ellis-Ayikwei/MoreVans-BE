# OTP System Quick Setup Guide

## 🚀 Quick Start

This guide will help you quickly set up and test the OTP (One-Time Password) system in your MoreVans application.

## 📋 Prerequisites

- Django project with User model already set up
- PostgreSQL database
- Email service configured (Gmail recommended)

## 🔧 Installation Steps

### 1. Database Migration
```bash
# Apply the OTP models migration
python manage.py migrate Authentication
```

### 2. Email Configuration

Create a `.env` file in your project root (if not exists):
```bash
# .env file
DJANGO_SECRET_KEY=your-secret-key-here
DEFAULT_FROM_EMAIL=your-email@gmail.com
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=465
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
EMAIL_USE_TLS=True
```

**Note**: For Gmail, you need to:
1. Enable 2-factor authentication
2. Generate an "App Password" for Django
3. Use the app password (not your regular password)

### 3. Settings Configuration

Ensure your `settings.py` includes:
```python
# Email backend
EMAIL_BACKEND = "apps.Authentication.email_backend.GmailSSLBackend"

# Template directories
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "apps", "Authentication", "templates"),
            # ... other dirs
        ],
        "APP_DIRS": True,
        # ...
    },
]
```

## 🧪 Testing the System

### 1. Test OTP Generation
```bash
python manage.py shell
```

```python
from apps.Authentication.otp_service import OTPService
from apps.User.models import User

# Get or create a test user
user = User.objects.filter(email='test@example.com').first()
if not user:
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )

# Generate OTP
otp = OTPService.generate_otp(user, 'signup_verification')
print(f"Generated OTP: {otp.code}")
print(f"Expires at: {otp.expires_at}")
```

### 2. Test Email Sending
```python
# Continuing in Django shell
email_sent = OTPService.send_otp_email(otp)
print(f"Email sent: {email_sent}")
```

### 3. Test OTP Verification
```python
# Verify the OTP
result = OTPService.verify_otp(
    otp.code, 
    'signup_verification', 
    'test@example.com'
)
print(f"Verification result: {result}")
```

## 🌐 API Testing

### Using curl

#### 1. Request OTP
```bash
curl -X POST http://localhost:8000/auth/otp/request/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "otp_type": "signup_verification"
  }'
```

#### 2. Verify OTP
```bash
curl -X POST http://localhost:8000/auth/otp/verify/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "otp_code": "123456",
    "otp_type": "signup_verification"
  }'
```

#### 3. Enhanced Registration
```bash
curl -X POST http://localhost:8000/auth/register-otp/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "securepass123",
    "password2": "securepass123",
    "first_name": "John",
    "last_name": "Doe",
    "otp_code": "123456"
  }'
```

### Using Postman/Insomnia

Import this collection:
```json
{
  "name": "OTP System Tests",
  "requests": [
    {
      "name": "Request OTP",
      "method": "POST",
      "url": "{{base_url}}/auth/otp/request/",
      "body": {
        "email": "test@example.com",
        "otp_type": "signup_verification"
      }
    },
    {
      "name": "Verify OTP",
      "method": "POST", 
      "url": "{{base_url}}/auth/otp/verify/",
      "body": {
        "email": "test@example.com",
        "otp_code": "{{otp_code}}",
        "otp_type": "signup_verification"
      }
    }
  ],
  "variables": {
    "base_url": "http://localhost:8000"
  }
}
```

## 🔍 Checking the Admin Interface

1. Create a superuser:
```bash
python manage.py createsuperuser
```

2. Start the server:
```bash
python manage.py runserver
```

3. Visit http://localhost:8000/admin/
4. Navigate to "Authentication" section
5. Check "OTPs" and "Login attempts" to see the data

## 🧹 Maintenance

### Clean up expired OTPs
```bash
# Dry run (see what would be deleted)
python manage.py cleanup_expired_otps --dry-run

# Actually clean up
python manage.py cleanup_expired_otps

# Keep only 3 days of login attempts
python manage.py cleanup_expired_otps --days=3
```

### Monitor OTP Usage
```python
# Django shell commands for monitoring
from apps.Authentication.models import OTP, LoginAttempt

# Check recent OTPs
recent_otps = OTP.objects.filter(
    created_at__gte=timezone.now() - timedelta(hours=24)
)
print(f"OTPs created in last 24h: {recent_otps.count()}")

# Check success rate
total_otps = OTP.objects.count()
verified_otps = OTP.objects.filter(is_verified=True).count()
success_rate = (verified_otps / total_otps * 100) if total_otps > 0 else 0
print(f"OTP success rate: {success_rate:.1f}%")
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Email not sending
```bash
# Test email configuration
python manage.py shell -c "
from django.core.mail import send_mail
try:
    send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
    print('Email sent successfully!')
except Exception as e:
    print(f'Email error: {e}')
"
```

#### 2. Template not found
```bash
# Check if templates exist
ls -la apps/Authentication/templates/emails/
```

Should show:
- `otp_verification.html`
- `otp_verification.txt`

#### 3. Migration issues
```bash
# Check migration status
python manage.py showmigrations Authentication

# If needed, fake apply the migration
python manage.py migrate Authentication --fake
```

#### 4. Rate limiting not working
```python
# Check in Django shell
from apps.Authentication.otp_service import OTPService

# Test rate limiting
result = OTPService.check_rate_limit('test@example.com', '127.0.0.1')
print(f"Rate limit check: {result}")
```

## 📱 Frontend Integration

### React Component Example
```jsx
import React, { useState } from 'react';

const OTPVerification = ({ email, onSuccess }) => {
  const [otpCode, setOtpCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const requestOTP = async () => {
    setLoading(true);
    try {
      const response = await fetch('/auth/otp/request/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email,
          otp_type: 'signup_verification'
        })
      });
      const data = await response.json();
      if (response.ok) {
        alert('OTP sent to your email!');
      } else {
        setError(data.detail || 'Failed to send OTP');
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const verifyOTP = async () => {
    setLoading(true);
    try {
      const response = await fetch('/auth/otp/verify/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email,
          otp_code: otpCode,
          otp_type: 'signup_verification'
        })
      });
      const data = await response.json();
      if (response.ok && data.verified) {
        onSuccess();
      } else {
        setError(data.detail || 'Invalid OTP');
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h3>Email Verification</h3>
      <p>We've sent a verification code to {email}</p>
      
      <button onClick={requestOTP} disabled={loading}>
        {loading ? 'Sending...' : 'Send OTP'}
      </button>
      
      <div>
        <input
          type="text"
          value={otpCode}
          onChange={(e) => setOtpCode(e.target.value)}
          placeholder="Enter 6-digit code"
          maxLength={6}
        />
        <button onClick={verifyOTP} disabled={!otpCode || loading}>
          {loading ? 'Verifying...' : 'Verify'}
        </button>
      </div>
      
      {error && <p style={{color: 'red'}}>{error}</p>}
    </div>
  );
};

export default OTPVerification;
```

## ✅ Verification Checklist

Before going to production, verify:

- [ ] Database migrations applied
- [ ] Email configuration working
- [ ] Templates rendering correctly
- [ ] Rate limiting functioning
- [ ] OTP generation and verification working
- [ ] Admin interface accessible
- [ ] Cleanup command working
- [ ] Error handling tested
- [ ] Security headers configured
- [ ] Logging enabled

## 🔒 Security Checklist

- [ ] SECRET_KEY is secure and not in version control
- [ ] Email credentials are in environment variables
- [ ] Rate limiting is enabled
- [ ] HTTPS is enabled in production
- [ ] Database access is restricted
- [ ] Admin interface is secured
- [ ] Logging is configured for monitoring

## 📞 Support

If you encounter issues:

1. Check the logs: `tail -f /var/log/django.log`
2. Test email configuration separately
3. Verify database connectivity
4. Check template file permissions
5. Review the comprehensive documentation in `OTP_SYSTEM_DOCUMENTATION.md`

---

**Next Steps**: Once the basic system is working, explore the advanced features in the full documentation, including risk-based authentication, enhanced security features, and performance optimizations.