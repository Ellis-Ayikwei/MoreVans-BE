from django.apps import AppConfig


class RoutesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.wastewise.routes'
    verbose_name = 'Collection Routes'

    def ready(self):
        import apps.wastewise.routes.signals