#!/usr/bin/env python
# ==========================================================================
# manage.py  |  Bookshop — file guide
# ==========================================================================
# Django's command-line entry point. Every management command runs through here.
#
#     python manage.py runserver          # dev server on http://127.0.0.1:8000/
#     python manage.py makemigrations     # model changes -> a migration file
#     python manage.py migrate            # apply migrations to db.sqlite3
#     python manage.py createsuperuser    # admin account for /admin/
#     python manage.py shell              # Python REPL with Django loaded
#     python manage.py check              # config sanity check
#
# It works by pointing DJANGO_SETTINGS_MODULE at myproject.settings, then handing
# the rest of argv to Django.
# ==========================================================================

"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
