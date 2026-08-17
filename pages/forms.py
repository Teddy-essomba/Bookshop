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





