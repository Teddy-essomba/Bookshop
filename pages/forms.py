# ==========================================================================
# pages/forms.py  |  Bookshop — file guide
# ==========================================================================
# BookForm - the HTML-page way of creating and editing a Book. (The API does the
# same job through pages/serializers.py.)
#
# It's a ModelForm built from Book, exposing only title, year_published and
# author - added_by and category are deliberately left out so a user can't set
# them; the view stamps added_by from request.user instead.
#
# Three levels of validation, which is the pattern the whole module uses:
#
#   clean_year_published()   ONE field. Rejects future years and anything before
#                            1440 (the printing press). Must RETURN the value -
#                            forget the return and the field silently becomes None.
#   clean()                  ACROSS fields. Rejects a book published before its
#                            author was born. Uses .get() because a field that
#                            already failed won't be in cleaned_data.
#   save(commit=False)       Normalises the title to Title Case before writing.
#
# Used as:  form = BookForm(request.POST)              # create
#           form = BookForm(request.POST, instance=b)  # edit - the only difference
#
# NOTE: save() also sets book.date_added, which is not a field on Book, so that
# line does nothing. Either add the field to models.py or delete the line.
# ==========================================================================

from django.core.exceptions import ValidationError
from datetime import date
from django.forms import ModelForm
from .models import Book


class BookForm(ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'year_published', 'author']


    def clean_year_published(self):
        year = self.cleaned_data['year_published']

        if year > date.today().year:
            raise ValidationError('The year published cannot be in the future.')

        if year < 1440:
            raise ValidationError('The printing press was not invented until 1440.')

        return year

    def clean(self):
        cleaned_data = super().clean()

        year = cleaned_data.get('year_published')
        author = cleaned_data.get('author')

        if year and author and year < author.birth_year:
            raise ValidationError(
                'A book cannot be published before its author was born.'
            )

        return cleaned_data


    def save(self, commit=True):
        book = super().save(commit=False)
        book.title = book.title.title()
        book.date_added = date.today()

        if commit:
            book.save()

        return book





