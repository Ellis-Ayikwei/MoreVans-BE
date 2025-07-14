#!/usr/bin/env python3
"""
Debug Gmail 421 error - find the real cause
"""

import smtplib
import socket
import time


def debug_gmail_421():
    """Debug the 421 error with detailed information"""

    EMAIL_HOST = "smtp.gmail.com"
    EMAIL_PORT = 587
    EMAIL_HOST_USER = "ellisarmahayikwei@gmail.com"
    EMAIL_HOST_PASSWORD = input("Enter your Gmail app password: ")

    print("=== Debugging Gmail 421 Error ===")
    print(f"Host: {EMAIL_HOST}")
    print(f"Port: {EMAIL_PORT}")
    print(f"User: {EMAIL_HOST_USER}")
    print("================================")

    # Test 1: Basic network connectivity
    print("\n1. Testing network connectivity...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((EMAIL_HOST, EMAIL_PORT))
        sock.close()

        if result == 0:
            print("✅ Network connectivity OK")
        else:
            print(f"❌ Network connectivity failed: {result}")
            print("This could be a firewall or network issue")
            return
    except Exception as e:
        print(f"❌ Network test failed: {e}")
        return

    # Test 2: SMTP connection without authentication
    print("\n2. Testing SMTP connection...")
    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10)
        print("✅ SMTP connection created")

        # Get server response
        print(f"Server response: {server.ehlo()}")

        # Test 3: TLS
        print("\n3. Testing TLS...")
        server.starttls()
        print("✅ TLS started")

        # Test 4: Authentication
        print("\n4. Testing authentication...")
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        print("✅ Authentication successful!")

        # Test 5: Send email
        print("\n5. Testing email send...")
        msg = f"Subject: Debug Test\n\nThis is a debug test email."
        server.sendmail(EMAIL_HOST_USER, EMAIL_HOST_USER, msg)
        print("✅ Email sent successfully!")

        server.quit()
        print("✅ All tests passed!")

    except smtplib.SMTPConnectError as e:
        print(f"❌ Connection failed: {e}")
        print(f"Error code: {e.smtp_code}")
        print(f"Error message: {e.smtp_error}")

        if e.smtp_code == 421:
            print("\n421 Error Analysis:")
            print("- Gmail is rejecting the connection before authentication")
            print("- This could be due to:")
            print("  1. Network/firewall blocking SMTP")
            print("  2. Gmail rate limiting")
            print("  3. Gmail security restrictions")
            print("  4. Too many failed attempts")

    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print(f"Error code: {e.smtp_code}")
        print(f"Error message: {e.smtp_error}")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"Error type: {type(e).__name__}")


def test_different_ports():
    """Test different Gmail ports"""
    print("\n=== Testing Different Gmail Ports ===")

    ports = [(587, "TLS"), (465, "SSL"), (25, "Standard")]

    for port, description in ports:
        print(f"\nTesting port {port} ({description})...")
        try:
            if port == 465:
                server = smtplib.SMTP_SSL("smtp.gmail.com", port, timeout=5)
            else:
                server = smtplib.SMTP("smtp.gmail.com", port, timeout=5)

            print(f"✅ Port {port} connection successful")
            server.quit()

        except Exception as e:
            print(f"❌ Port {port} failed: {e}")


if __name__ == "__main__":
    debug_gmail_421()
    test_different_ports()
