# ==========================================================================
# pages/models.py  |  Bookshop — file guide
# ==========================================================================
# The database schema. Each class is a table, each attribute is a column, each
# instance is a row. Django's ORM turns these into SQL so we never write it.
#
#   Author            name, birth_year, country
#   Book              title, year_published, category (default "general")
#                     -> author    FK Author, on_delete=CASCADE
#                                  (delete an author and their books go too)
#                     -> added_by  FK User, on_delete=SET_NULL, null=True
#                                  (a user can leave without deleting their books;
#                                   this is the field ownership checks read)
#   ReadingListItem   one user's saved book - notes, priority, added_at
#                     unique_together ('user', 'book')  -> can't save a book twice
#                     ordering ['-priority', '-added_at'] -> default sort order
#                     related_name='reading_list' -> user.reading_list.all()
#
# __str__ on each model is what the admin and the shell display; without it you
# just see "Book object (1)".
#
# AFTER ANY CHANGE IN THIS FILE:
#     python manage.py makemigrations
#     python manage.py migrate
# ==========================================================================

from django.db import models
from django.contrib.auth.models import User


# Create your models here.

class Author(models.Model):
    name = models.CharField(max_length=100)
    birth_year = models.IntegerField()
    country = models.CharField(max_length=50)


    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200)
    year_published = models.IntegerField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    category = models.CharField(max_length=50, default="general")
    added_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        # null=True  -> the DATABASE column may be NULL (a user can be
        #               deleted without taking their books with them).
        # blank=True -> FORMS may leave it empty. Without this the admin's
        #               "Add book" page refuses to save until you pick a
        #               user, even though the column allows NULL.
        null=True, blank=True,
    )


    def __str__(self):
        return self.title


class ReadingListItem(models.Model):
    """A book on a user's personal reading list."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reading_list')
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    priority = models.IntegerField(default=0)  # Higher = more important

    class Meta:
        unique_together = ['user', 'book']  # Can't add same book twice
        ordering = ['-priority', '-added_at']

    def __str__(self):
        return f"{self.user.username}'s list: {self.book.title}"



