from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Runs a list of management commands in sequence.'

    def add_arguments(self, parser):
        parser.add_argument(
            'commands',
            nargs='+',
            type=str,
            help='List of management commands to run in order',
        )

    def handle(self, *args, **options):
        commands = options.get('commands', [])
        if not commands:
            self.stdout.write(self.style.WARNING('No commands specified.'))
            return

        for cmd_name in commands:
            self.stdout.write(self.style.NOTICE(f'🔧 Running: {cmd_name}'))
            try:
                call_command(cmd_name)
            except Exception as e:
                raise CommandError(f'❌ Error running "{cmd_name}": {e}')

        self.stdout.write(self.style.SUCCESS('✅ All commands executed successfully.'))
