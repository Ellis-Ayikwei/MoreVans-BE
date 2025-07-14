"""
Custom email backend for Gmail SSL
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings


class GmailSSLBackend(BaseEmailBackend):
    """
    Custom email backend for Gmail with SSL support
    """

    def send_messages(self, email_messages):
        """
        Send messages using Gmail SMTP with SSL
        """
        if not email_messages:
            return 0

        num_sent = 0

        try:
            # Create SSL connection
            server = smtplib.SMTP_SSL(
                settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10
            )

            # Login
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)

            # Send each message
            for message in email_messages:
                try:
                    # Create email
                    msg = MIMEMultipart()
                    msg["From"] = message.from_email
                    msg["To"] = ", ".join(message.to)
                    msg["Subject"] = message.subject

                    # Add body
                    if message.body:
                        msg.attach(MIMEText(message.body, "plain"))

                    # Send email
                    server.sendmail(message.from_email, message.to, msg.as_string())
                    num_sent += 1

                except Exception as e:
                    print(f"Failed to send email: {e}")
                    continue

            server.quit()

        except Exception as e:
            print(f"SMTP connection failed: {e}")
            raise

        return num_sent
