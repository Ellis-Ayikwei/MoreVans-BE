#!/usr/bin/env python3
"""
Test real SMTP connection with actual credentials
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def test_real_smtp():
    """Test real SMTP connection"""

    # Replace these with your actual credentials
    EMAIL_HOST = "smtp.gmail.com"
    EMAIL_PORT = 587
    EMAIL_HOST_USER = "ellisarmahayikwei@gmail.com"
    EMAIL_HOST_PASSWORD = input(
        "Enter your Gmail app password: "
    )  # Will prompt for password
    EMAIL_USE_TLS = True

    print("=== Testing Real SMTP Connection ===")
    print(f"Host: {EMAIL_HOST}")
    print(f"Port: {EMAIL_PORT}")
    print(f"User: {EMAIL_HOST_USER}")
    print(f"TLS: {EMAIL_USE_TLS}")
    print("================================")

    try:
        # Step 1: Create SMTP connection
        print("1. Creating SMTP connection...")
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10)
        print("✅ SMTP connection created")

        # Step 2: Start TLS
        print("2. Starting TLS...")
        server.starttls()
        print("✅ TLS started")

        # Step 3: Login
        print("3. Attempting login...")
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        print("✅ Login successful!")

        # Step 4: Send test email
        print("4. Sending test email...")
        msg = MIMEMultipart()
        msg["From"] = EMAIL_HOST_USER
        msg["To"] = EMAIL_HOST_USER  # Send to self for testing
        msg["Subject"] = "Real SMTP Test"

        body = "This is a test email to verify real SMTP is working."
        msg.attach(MIMEText(body, "plain"))

        text = msg.as_string()
        server.sendmail(EMAIL_HOST_USER, EMAIL_HOST_USER, text)
        print("✅ Test email sent successfully!")

        # Step 5: Close connection
        server.quit()
        print("✅ SMTP connection closed")
        print("🎉 Real SMTP is working! You can now use this in Django.")

        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("\nSolutions:")
        print("1. Make sure 2-factor authentication is enabled")
        print("2. Generate a new app password")
        print("3. Use the app password, not your regular password")
        return False

    except smtplib.SMTPConnectError as e:
        print(f"❌ Connection failed: {e}")
        print("\nSolutions:")
        print("1. Check your internet connection")
        print("2. Try from a different network")
        print("3. Gmail might be blocking the connection")
        return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"Error type: {type(e).__name__}")
        return False


if __name__ == "__main__":
    test_real_smtp()
