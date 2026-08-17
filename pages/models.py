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
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)


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



