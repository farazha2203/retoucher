from django.apps import AppConfig


class OperationsHubConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "operations_hub"
    verbose_name = "مرکز عملیات پنل"

    def ready(self):
        from . import signals  # noqa: F401
