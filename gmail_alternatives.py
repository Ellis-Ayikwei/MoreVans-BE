#!/usr/bin/env python3
"""
Test different Gmail SMTP configurations
"""

import smtplib
from email.mime.text import MIMEText


def test_gmail_configurations():
    """Test different Gmail SMTP configurations"""

    EMAIL_HOST_USER = "ellisarmahayikwei@gmail.com"
    EMAIL_HOST_PASSWORD = "your_new_app_password_here"  # Replace with your password

    # Configuration 1: Standard Gmail SMTP (Port 587, TLS)
    config1 = {
        "name": "Gmail SMTP (Port 587, TLS)",
        "host": "smtp.gmail.com",
        "port": 587,
        "use_tls": True,
        "use_ssl": False,
    }

    # Configuration 2: Gmail SMTP (Port 465, SSL)
    config2 = {
        "name": "Gmail SMTP (Port 465, SSL)",
        "host": "smtp.gmail.com",
        "port": 465,
        "use_tls": False,
        "use_ssl": True,
    }

    # Configuration 3: Gmail SMTP (Port 587, No TLS)
    config3 = {
        "name": "Gmail SMTP (Port 587, No TLS)",
        "host": "smtp.gmail.com",
        "port": 587,
        "use_tls": False,
        "use_ssl": False,
    }

    configurations = [config1, config2, config3]

    for config in configurations:
        print(f"\n=== Testing: {config['name']} ===")
        print(f"Host: {config['host']}:{config['port']}")
        print(f"TLS: {config['use_tls']}, SSL: {config['use_ssl']}")

        try:
            if config["use_ssl"]:
                server = smtplib.SMTP_SSL(config["host"], config["port"], timeout=10)
            else:
                server = smtplib.SMTP(config["host"], config["port"], timeout=10)

            print("✅ Connection created")

            if config["use_tls"]:
                server.starttls()
                print("✅ TLS started")

            server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
            print("✅ Login successful!")

            # Send test email
            msg = f"Subject: Test from {config['name']}\n\nThis is a test email."
            server.sendmail(EMAIL_HOST_USER, EMAIL_HOST_USER, msg)
            print("✅ Email sent successfully!")

            server.quit()
            print(f"🎉 {config['name']} is working!")
            return config  # Return the working configuration

        except Exception as e:
            print(f"❌ Failed: {e}")
            print(f"Error type: {type(e).__name__}")

    print("\n❌ All configurations failed. Try the following:")
    print("1. Check your internet connection")
    print("2. Try from a different network")
    print("3. Verify your app password is correct")
    print("4. Check if Gmail account has any restrictions")
    return None


if __name__ == "__main__":
    test_gmail_configurations()
