from django.apps import AppConfig

class SystemConfig(AppConfig):
    """
    AppConfig for the System application. Handles core operational views (like healthchecks).
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'system'