from django.apps import AppConfig


class SensorsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.wastewise.sensors'
    verbose_name = 'IoT Sensors'

    def ready(self):
        import apps.wastewise.sensors.signals