"""
Test script to demonstrate OTP system functionality
Run this after applying migrations
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.User.models import User
from apps.Authentication.models import OTP, UserVerification
from apps.Authentication.utils import OTPEmailService, mask_email
from django.utils import timezone


def test_otp_system():
    print("=== Testing OTP System ===\n")
    
    # 1. Create a test user
    print("1. Creating test user...")
    test_email = "test@example.com"
    
    # Check if user already exists
    user = User.objects.filter(email=test_email).first()
    if not user:
        user = User.objects.create_user(
            email=test_email,
            password="testpassword123",
            first_name="Test",
            last_name="User",
            is_active=False  # Inactive until verified
        )
        print(f"   ✓ User created: {user.email}")
    else:
        print(f"   ✓ User already exists: {user.email}")
    
    # 2. Generate OTP for signup
    print("\n2. Generating OTP for signup verification...")
    otp = OTP.generate_otp(user, 'signup')
    print(f"   ✓ OTP generated: {otp.otp_code}")
    print(f"   ✓ Expires at: {otp.expires_at}")
    print(f"   ✓ Masked email: {mask_email(user.email)}")
    
    # 3. Test OTP validation
    print("\n3. Testing OTP validation...")
    
    # Test with wrong OTP
    wrong_otp = "000000"
    print(f"   - Testing with wrong OTP: {wrong_otp}")
    test_otp = OTP.objects.get(id=otp.id)  # Get fresh instance
    result = test_otp.verify(wrong_otp)
    print(f"   ✓ Wrong OTP rejected: {not result}")
    print(f"   ✓ Attempts used: {test_otp.attempts}/{test_otp.max_attempts}")
    
    # Test with correct OTP
    print(f"   - Testing with correct OTP: {otp.otp_code}")
    test_otp = OTP.objects.get(id=otp.id)  # Get fresh instance
    result = test_otp.verify(otp.otp_code)
    print(f"   ✓ Correct OTP accepted: {result}")
    print(f"   ✓ OTP marked as used: {test_otp.is_used}")
    
    # 4. Create UserVerification
    print("\n4. Creating user verification record...")
    verification, created = UserVerification.objects.get_or_create(user=user)
    verification.email_verified = True
    verification.email_verified_at = timezone.now()
    verification.save()
    print(f"   ✓ Email verified: {verification.email_verified}")
    print(f"   ✓ Verified at: {verification.email_verified_at}")
    
    # 5. Activate user
    print("\n5. Activating user account...")
    user.is_active = True
    user.save()
    print(f"   ✓ User activated: {user.is_active}")
    
    # 6. Test login OTP
    print("\n6. Testing login with OTP...")
    login_otp = OTP.generate_otp(user, 'login')
    print(f"   ✓ Login OTP generated: {login_otp.otp_code}")
    
    # 7. Test password reset OTP
    print("\n7. Testing password reset OTP...")
    reset_otp = OTP.generate_otp(user, 'password_reset')
    print(f"   ✓ Password reset OTP generated: {reset_otp.otp_code}")
    
    # 8. Show OTP history
    print("\n8. OTP History for user:")
    otps = OTP.objects.filter(user=user).order_by('-created_at')
    for otp in otps:
        print(f"   - Type: {otp.otp_type}, Code: {otp.otp_code}, Used: {otp.is_used}, Created: {otp.created_at}")
    
    print("\n=== OTP System Test Complete ===")


def test_email_template():
    """Test email template rendering"""
    print("\n=== Testing Email Template ===\n")
    
    from django.template.loader import render_to_string
    from datetime import datetime
    
    # Test context
    context = {
        'user_name': 'John Doe',
        'otp_code': '123456',
        'validity_minutes': 10,
        'app_name': 'MoveVans',
        'current_year': datetime.now().year,
        'subject': 'Verify Your Email',
        'message': 'Thank you for signing up! Please use the code below to verify your email address.',
        'action_url': 'https://example.com/verify',
        'action_text': 'Verify Now'
    }
    
    try:
        # Render HTML template
        html_content = render_to_string('emails/otp_verification.html', context)
        print("✓ HTML template rendered successfully")
        print(f"  Length: {len(html_content)} characters")
        
        # Render text template
        text_content = render_to_string('emails/otp_verification.txt', context)
        print("✓ Text template rendered successfully")
        print(f"  Length: {len(text_content)} characters")
        
        # Show a preview of the text email
        print("\n--- Text Email Preview ---")
        print(text_content[:500] + "..." if len(text_content) > 500 else text_content)
        
    except Exception as e:
        print(f"✗ Error rendering template: {e}")


if __name__ == "__main__":
    try:
        test_otp_system()
        test_email_template()
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()