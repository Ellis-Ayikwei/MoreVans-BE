from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.Authentication.otp_service import OTPService
from apps.Authentication.models import OTP, LoginAttempt
from datetime import timedelta


class Command(BaseCommand):
    help = 'Clean up expired OTP records and old login attempts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to keep login attempt records (default: 7)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days_to_keep = options['days']

        self.stdout.write(
            self.style.SUCCESS(f'Starting cleanup (dry_run: {dry_run})...')
        )

        # Clean up expired OTPs
        if dry_run:
            expired_otps = OTP.objects.filter(expires_at__lt=timezone.now())
            otp_count = expired_otps.count()
            self.stdout.write(f'Would delete {otp_count} expired OTP records')
        else:
            otp_count = OTPService.cleanup_expired_otps()
            self.stdout.write(
                self.style.SUCCESS(f'Deleted {otp_count} expired OTP records')
            )

        # Clean up old login attempts
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        if dry_run:
            old_attempts = LoginAttempt.objects.filter(attempt_time__lt=cutoff_date)
            attempt_count = old_attempts.count()
            self.stdout.write(f'Would delete {attempt_count} old login attempt records')
        else:
            attempt_count = LoginAttempt.objects.filter(
                attempt_time__lt=cutoff_date
            ).delete()[0]
            self.stdout.write(
                self.style.SUCCESS(f'Deleted {attempt_count} old login attempt records')
            )

        # Show statistics
        total_otps = OTP.objects.count()
        total_attempts = LoginAttempt.objects.count()
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write('CLEANUP SUMMARY')
        self.stdout.write('='*50)
        self.stdout.write(f'Remaining OTP records: {total_otps}')
        self.stdout.write(f'Remaining login attempt records: {total_attempts}')
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS('\nCleanup completed successfully!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('\nDry run completed. Use without --dry-run to actually delete records.')
            )