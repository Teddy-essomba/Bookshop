# ==========================================================================
# pages/admin.py  |  Bookshop — file guide
# ==========================================================================
# Registers models with the Django admin at /admin/, so rows can be added and
# edited through a UI without building any forms.
#
# Run `python manage.py createsuperuser` once to get a login. The readable
# names in the admin lists come from the __str__ methods in models.py.
#
# list_display / list_filter / search_fields are optional niceties -- they
# control the columns, the sidebar filters and the search box on the list page.
# ==========================================================================

from django.contrib import admin

from .models import Author, Book, ReadingListItem


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'birth_year', 'country')
    search_fields = ('name', 'country')


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'year_published', 'category', 'added_by')
    list_filter = ('category', 'year_published')
    search_fields = ('title',)


@admin.register(ReadingListItem)
class ReadingListItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'priority', 'added_at')
    list_filter = ('user',)
