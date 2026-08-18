# ==========================================================================
# myproject/wsgi.py  |  Bookshop — file guide
# ==========================================================================
# WSGI entry point - the handle a production server (gunicorn, mod_wsgi, etc.)
# grabs to serve this project synchronously. Not used by runserver in dev; you
# almost never edit this file.
# ==========================================================================

"""
WSGI config for myproject project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

application = get_wsgi_application()
