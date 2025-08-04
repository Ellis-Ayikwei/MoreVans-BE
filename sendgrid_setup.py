#!/usr/bin/env python3
"""
SendGrid Email Setup - Using Web API for better reliability
"""

# Install required packages:
# pip install sendgrid django-sendgrid-v5

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def setup_sendgrid():
    """Set up SendGrid for email sending using Web API"""

    # Get API key from environment or input
    api_key = os.getenv("SENDGRID_API_KEY")
    if not api_key:
        api_key = input("Enter your SendGrid API key: ")

    print("=== SendGrid Web API Setup ===")
    print(f"API Key: {'*' * len(api_key) if api_key else 'None'}")

    try:
        # Create message
        message = Mail(
            from_email="noreply@morevans.com",  # Update with your verified sender
            to_emails="ellisarmahayikwei@gmail.com",
            subject="SendGrid Web API Test Email",
            html_content="<strong>This is a test email from SendGrid Web API</strong>",
        )

        # Send email
        sg = SendGridAPIClient(api_key=api_key)
        response = sg.send(message)

        print(f"✅ SendGrid email sent successfully!")
        print(f"Status code: {response.status_code}")
        print(f"Headers: {response.headers}")

        return True

    except Exception as e:
        print(f"❌ SendGrid error: {e}")
        return False


def get_django_settings():
    """Get Django settings for SendGrid Web API"""
    print("\n=== Django Settings for SendGrid Web API ===")
    print("Add these to your settings.py:")
    print(
        """
# SendGrid Email Configuration (Web API)
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
DEFAULT_FROM_EMAIL = 'noreply@morevans.com'  # Your verified sender
SENDGRID_TRACK_CLICKS_PLAIN = False
SENDGRID_TRACK_CLICKS_HTML = False
SENDGRID_TRACK_OPENS = False

# Add to your .env file:
# SENDGRID_API_KEY=your_sendgrid_api_key_here
# DEFAULT_FROM_EMAIL=noreply@morevans.com
"""
    )


def create_env_example():
    """Create example environment file"""
    env_content = """# SendGrid Configuration
SENDGRID_API_KEY=your_sendgrid_api_key_here
DEFAULT_FROM_EMAIL=noreply@morevans.com
"""

    with open(".env.example", "w") as f:
        f.write(env_content)

    print("✅ Created .env.example file")


if __name__ == "__main__":
    print("SendGrid Web API Setup:")
    print("1. Sign up at https://sendgrid.com/ (free tier available)")
    print("2. Verify your sender identity in SendGrid dashboard")
    print("3. Get your API key from SendGrid dashboard")
    print("4. Install required packages: pip install sendgrid django-sendgrid-v5")
    print("5. Add SENDGRID_API_KEY to your .env file")

    if setup_sendgrid():
        get_django_settings()
        create_env_example()
    else:
        print("Failed to set up SendGrid")
        print("\nTroubleshooting:")
        print("- Make sure your API key is correct")
        print("- Verify your sender email in SendGrid dashboard")
        print("- Check SendGrid API status")
