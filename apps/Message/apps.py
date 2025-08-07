from django.apps import AppConfig


class MessageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.Message'

    def ready(self):
        import apps.Message.signals
        # Connect signals manually to avoid circular imports
        from apps.Message.signals import connect_signals
        connect_signals()
