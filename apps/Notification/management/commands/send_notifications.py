from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.Notification.models import Notification
from apps.Notification.services import NotificationService
from apps.User.models import User


class Command(BaseCommand):
    help = "Send notifications and manage notification system"

    def add_arguments(self, parser):
        parser.add_argument(
            "--send-scheduled",
            action="store_true",
            help="Send all scheduled notifications that are due",
        )
        parser.add_argument(
            "--test-email",
            type=str,
            help="Send a test notification to specified email",
        )
        parser.add_argument(
            "--cleanup-old",
            type=int,
            default=30,
            help="Delete read notifications older than specified days (default: 30)",
        )
        parser.add_argument(
            "--stats",
            action="store_true",
            help="Show notification statistics",
        )
        parser.add_argument(
            "--maintenance",
            action="store_true",
            help="Send system maintenance notification to all users",
        )
        parser.add_argument(
            "--maintenance-date",
            type=str,
            help="Maintenance date (YYYY-MM-DD HH:MM)",
        )
        parser.add_argument(
            "--maintenance-duration",
            type=str,
            default="2 hours",
            help="Expected maintenance duration",
        )

    def handle(self, *args, **options):
        if options["send_scheduled"]:
            self.send_scheduled_notifications()

        if options["test_email"]:
            self.send_test_notification(options["test_email"])

        if options["cleanup_old"]:
            self.cleanup_old_notifications(options["cleanup_old"])

        if options["stats"]:
            self.show_statistics()

        if options["maintenance"]:
            self.send_maintenance_notification(
                options.get("maintenance_date"), options.get("maintenance_duration")
            )

    def send_scheduled_notifications(self):
        """Send all scheduled notifications that are due"""
        now = timezone.now()
        scheduled_notifications = Notification.objects.filter(
            scheduled_for__lte=now, delivered_at__isnull=True
        )

        count = 0
        for notification in scheduled_notifications:
            try:
                NotificationService.send_notification(notification)
                count += 1
                self.stdout.write(f"Sent scheduled notification {notification.id}")
            except Exception as e:
                self.stderr.write(
                    f"Failed to send notification {notification.id}: {str(e)}"
                )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully sent {count} scheduled notifications")
        )

    def send_test_notification(self, email):
        """Send a test notification to specified email"""
        try:
            user = User.objects.get(email=email)
            notification = NotificationService.create_notification(
                user=user,
                notification_type="system",
                title="Test Notification",
                message="This is a test notification to verify the email system is working correctly.",
                priority="normal",
                channels=["in_app", "email"],
                send_immediately=True,
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Test notification sent to {email} (ID: {notification.id})"
                )
            )
        except User.DoesNotExist:
            self.stderr.write(f"User with email {email} not found")
        except Exception as e:
            self.stderr.write(f"Failed to send test notification: {str(e)}")

    def cleanup_old_notifications(self, days):
        """Delete old read notifications"""
        cutoff_date = timezone.now() - timedelta(days=days)
        old_notifications = Notification.objects.filter(
            read=True, read_at__lt=cutoff_date
        )

        count = old_notifications.count()
        old_notifications.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {count} old notifications (older than {days} days)"
            )
        )

    def show_statistics(self):
        """Show notification system statistics"""
        total = Notification.objects.count()
        unread = Notification.objects.filter(read=False).count()
        today = timezone.now().date()
        today_sent = Notification.objects.filter(created_at__date=today).count()

        # Count by type
        type_counts = {}
        for notification_type, _ in Notification.NOTIFICATION_TYPES:
            count = Notification.objects.filter(
                notification_type=notification_type
            ).count()
            if count > 0:
                type_counts[notification_type] = count

        # Count by priority
        priority_counts = {}
        for priority, _ in Notification.PRIORITY_LEVELS:
            count = Notification.objects.filter(priority=priority).count()
            if count > 0:
                priority_counts[priority] = count

        # Email delivery stats
        email_sent = Notification.objects.filter(email_sent=True).count()
        email_pending = Notification.objects.filter(
            delivery_channels__contains=["email"], email_sent=False
        ).count()

        self.stdout.write("=== NOTIFICATION STATISTICS ===")
        self.stdout.write(f"Total notifications: {total}")
        self.stdout.write(f"Unread notifications: {unread}")
        self.stdout.write(f"Sent today: {today_sent}")
        self.stdout.write(f"Email sent: {email_sent}")
        self.stdout.write(f"Email pending: {email_pending}")

        self.stdout.write("\n=== BY TYPE ===")
        for ntype, count in type_counts.items():
            self.stdout.write(f"{ntype}: {count}")

        self.stdout.write("\n=== BY PRIORITY ===")
        for priority, count in priority_counts.items():
            self.stdout.write(f"{priority}: {count}")

    def send_maintenance_notification(self, maintenance_date, duration):
        """Send system maintenance notification to all users"""
        from apps.Notification.signals import send_system_maintenance_notification

        maintenance_info = {
            "date": maintenance_date or "TBD",
            "duration": duration,
            "type": "scheduled_maintenance",
        }

        if maintenance_date:
            try:
                from datetime import datetime

                maintenance_dt = datetime.strptime(maintenance_date, "%Y-%m-%d %H:%M")
                # Set expiration to 1 hour after maintenance starts
                maintenance_info["expires_at"] = maintenance_dt + timedelta(hours=1)
            except ValueError:
                self.stderr.write("Invalid date format. Use YYYY-MM-DD HH:MM")
                return

        count = send_system_maintenance_notification(maintenance_info)
        self.stdout.write(
            self.style.SUCCESS(f"Sent maintenance notification to {count} users")
        )
