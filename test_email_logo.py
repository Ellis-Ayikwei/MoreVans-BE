#!/usr/bin/env python3
"""
Test script to demonstrate the email template with embedded logo
"""

import os
import sys
import django
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from django.template.loader import render_to_string
from apps.Authentication.utils import OTPEmailService


def test_email_template():
    """Test the email template with embedded logo"""

    # Generate logo
    logo_data_url = OTPEmailService.get_logo_data_url("MV", "#2E2787", 80)

    # Create test context
    context = {
        "user_name": "John Doe",
        "otp_code": "123456",
        "validity_minutes": 10,
        "app_name": "MoreVans",
        "message": "Please use this code to verify your email address.",
        "current_year": 2024,
        "logo_svg_base64": logo_data_url.split(",")[
            1
        ],  # Remove the data:image/svg+xml;base64, prefix
    }

    # Render the template
    html_content = render_to_string("emails/otp_verification.html", context)

    # Save to file for preview
    with open("email_preview.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print("✅ Email template generated successfully!")
    print("📧 Preview saved to: email_preview.html")
    print("🎨 Logo is embedded as base64 SVG")
    print("🔗 You can open email_preview.html in your browser to see the result")

    # Show logo generation info
    print(f"\n📊 Logo Info:")
    print(f"   - Text: MV")
    print(f"   - Color: #2E2787")
    print(f"   - Size: 80px")
    print(f"   - Format: SVG (embedded)")
    print(f"   - Base64 length: {len(logo_data_url.split(',')[1])} characters")


if __name__ == "__main__":
    test_email_template()
