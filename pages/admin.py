# ==========================================================================
# pages/admin.py  |  Bookshop — file guide
# ==========================================================================
# Registers models with the Django admin at /admin/, so we can add and edit rows
# through a UI without building a single form.
#
# Author and Book are registered. ReadingListItem is NOT - add
# admin.site.register(ReadingListItem) if you want to inspect reading lists here.
#
# Run `python manage.py createsuperuser` once to get a login. The readable names
# in the admin lists come from the __str__ methods in models.py.
# ==========================================================================

from django.contrib import admin
from .models import Author, Book

# Register your models here.



admin.site.register(Author)
admin.site.register(Book)