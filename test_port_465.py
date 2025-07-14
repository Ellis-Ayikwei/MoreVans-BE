#!/usr/bin/env python3
"""
Test Gmail SMTP with port 465 and SSL
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def test_port_465():
    """Test Gmail SMTP with port 465 and SSL"""

    EMAIL_HOST = "smtp.gmail.com"
    EMAIL_PORT = 465
    EMAIL_HOST_USER = "ellisarmahayikwei@gmail.com"
    EMAIL_HOST_PASSWORD = "sdak cche veza wbdn"  # Your app password
    EMAIL_USE_SSL = True

    print("=== Testing Gmail SMTP (Port 465, SSL) ===")
    print(f"Host: {EMAIL_HOST}")
    print(f"Port: {EMAIL_PORT}")
    print(f"User: {EMAIL_HOST_USER}")
    print(f"SSL: {EMAIL_USE_SSL}")
    print("================================")

    try:
        # Create SMTP_SSL connection
        print("1. Creating SMTP_SSL connection...")
        server = smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT, timeout=10)
        print("✅ SMTP_SSL connection created")

        # Login
        print("2. Attempting login...")
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        print("✅ Login successful!")

        # Send test email
        print("3. Sending test email...")
        msg = MIMEMultipart()
        msg["From"] = EMAIL_HOST_USER
        msg["To"] = EMAIL_HOST_USER  # Send to self for testing
        msg["Subject"] = "Port 465 SSL Test"

        body = "This is a test email using port 465 with SSL."
        msg.attach(MIMEText(body, "plain"))

        text = msg.as_string()
        server.sendmail(EMAIL_HOST_USER, EMAIL_HOST_USER, text)
        print("✅ Test email sent successfully!")

        # Close connection
        server.quit()
        print("✅ SMTP connection closed")
        print("🎉 Port 465 SSL is working! This should work in Django.")

    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Error type: {type(e).__name__}")


if __name__ == "__main__":
    test_port_465()
