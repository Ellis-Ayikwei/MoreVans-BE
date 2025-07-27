from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.wastewise.users'
    verbose_name = 'Users'

    def ready(self):
        import apps.wastewise.users.signals