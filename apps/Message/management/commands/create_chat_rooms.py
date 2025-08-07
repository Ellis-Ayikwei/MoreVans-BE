"""
Management command to create chat rooms for existing objects
"""
from django.core.management.base import BaseCommand
from apps.Message.chat_services import ChatAutomationService


class Command(BaseCommand):
    help = 'Create chat rooms for existing requests, jobs, and bids that don\'t have them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run in dry-run mode without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('Running in dry-run mode - no changes will be made')
            )
        
        try:
            if not dry_run:
                ChatAutomationService.auto_create_chat_rooms()
                self.stdout.write(
                    self.style.SUCCESS('Successfully created chat rooms for existing objects')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('Dry-run completed - would create chat rooms for existing objects')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating chat rooms: {str(e)}')
            )