# ==========================================================================
# pages/apps.py  |  Bookshop — file guide
# ==========================================================================
# App config for the 'pages' app. Django autogenerates this; the only thing it
# does here is set the default primary-key type to BigAutoField.
# ==========================================================================

from django.apps import AppConfig


class PagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pages'
