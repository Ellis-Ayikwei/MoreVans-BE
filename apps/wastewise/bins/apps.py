from django.apps import AppConfig


class BinsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.wastewise.bins'
    verbose_name = 'Waste Bins'

    def ready(self):
        import apps.wastewise.bins.signals