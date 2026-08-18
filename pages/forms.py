# ==========================================================================
# pages/forms.py  |  Bookshop — file guide
# ==========================================================================
# BookForm -- the HTML-page way of creating and editing a Book.
# (The API does the same job through pages/serializers.py.)
#
# It is a ModelForm built from Book, exposing only title, year_published and
# author. `added_by` and `category` are deliberately left out so a user cannot
# set them; add_book() in views.py stamps added_by from request.user instead.
#
# Three levels of validation -- the pattern the whole module uses:
#
#   clean_year_published()   ONE field.    Must RETURN the value.
#   clean()                  ACROSS fields. Uses .get(), because a field that
#                            already failed won't be in cleaned_data.
#   save(commit=False)       Last-second tidying before the row is written.
#
# Used as:  BookForm(request.POST)                 # create
#           BookForm(request.POST, instance=book)  # edit -- the only difference
# ==========================================================================

from datetime import date

from django.core.exceptions import ValidationError
from django.forms import ModelForm

from .models import Book


class BookForm(ModelForm):
    class Meta:
        model = Book
        # Listed explicitly, never '__all__' -- otherwise a field added to the
        # model later silently becomes user-editable.
        fields = ['title', 'year_published', 'author']

    def clean_year_published(self):
        """
        Field-level validation.

        Two ways to break this silently: misspell the method name (Django then
        never calls it), or forget the `return` (the field becomes None and
        bad data is saved with no error shown).
        """
        year = self.cleaned_data['year_published']

        if year > date.today().year:
            raise ValidationError('The year published cannot be in the future.')

        if year < 1440:
            raise ValidationError('The printing press was not invented until 1440.')

        return year

    def clean(self):
        """Cross-field validation -- needs two fields at once, so it goes here."""
        cleaned_data = super().clean()

        year = cleaned_data.get('year_published')
        author = cleaned_data.get('author')

        if year and author and year < author.birth_year:
            raise ValidationError(
                'A book cannot be published before its author was born.'
            )

        return cleaned_data

    def save(self, commit=True):
        """
        Normalise the title before saving.

        commit=False returns the unsaved instance so it can be modified first.
        Only set attributes that are REAL model fields here -- assigning
        something that isn't a field (e.g. self.date_added) does nothing at
        all: it lives on the Python object and is dropped on save.
        """
        book = super().save(commit=False)
        book.title = book.title.title()

        if commit:
            book.save()

        return book
