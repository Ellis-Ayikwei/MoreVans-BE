#!/usr/bin/env python3
"""
Test SMTP connection for debugging email issues
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def test_smtp_connection():
    """Test SMTP connection with current settings"""

    # Email settings (same as in Django settings)
    EMAIL_HOST = "smtp.gmail.com"
    EMAIL_PORT = 587
    EMAIL_HOST_USER = "ellisarmahayikwei@gmail.com"
    EMAIL_HOST_PASSWORD = "trxe mjsy kyhn yurw"
    EMAIL_USE_TLS = True

    print("=== Testing SMTP Connection ===")
    print(f"Host: {EMAIL_HOST}")
    print(f"Port: {EMAIL_PORT}")
    print(f"User: {EMAIL_HOST_USER}")
    print(
        f"Password: {'*' * len(EMAIL_HOST_PASSWORD) if EMAIL_HOST_PASSWORD else 'None'}"
    )
    print(f"TLS: {EMAIL_USE_TLS}")
    print("==============================")

    try:
        # Create SMTP connection
        print("Creating SMTP connection...")
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        print("SMTP connection created successfully")

        # Start TLS
        if EMAIL_USE_TLS:
            print("Starting TLS...")
            server.starttls()
            print("TLS started successfully")

        # Login
        print("Attempting login...")
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        print("Login successful!")

        # Test sending a simple email
        print("Testing email send...")
        msg = MIMEMultipart()
        msg["From"] = EMAIL_HOST_USER
        msg["To"] = EMAIL_HOST_USER  # Send to self for testing
        msg["Subject"] = "SMTP Test"

        body = "This is a test email to verify SMTP configuration."
        msg.attach(MIMEText(body, "plain"))

        text = msg.as_string()
        server.sendmail(EMAIL_HOST_USER, EMAIL_HOST_USER, text)
        print("Test email sent successfully!")

        # Close connection
        server.quit()
        print("SMTP connection closed")
        print("✅ SMTP configuration is working!")

    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("This usually means the app password is incorrect or expired.")
        print("Please generate a new Gmail app password.")

    except smtplib.SMTPConnectError as e:
        print(f"❌ Connection failed: {e}")
        print("This could be due to:")
        print("- Network/firewall issues")
        print("- Gmail blocking the connection")
        print("- Incorrect host/port settings")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"Error type: {type(e).__name__}")


if __name__ == "__main__":
    test_smtp_connection()
