from django.apps import AppConfig


class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.chat'
    verbose_name = 'Chat'

    def ready(self):
        """Importar signals cuando la app esté lista."""
        from . import signals  # noqa
