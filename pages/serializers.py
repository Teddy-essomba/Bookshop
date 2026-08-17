# pages/serializers.py
from rest_framework import serializers
from .models import Author, Book, ReadingListItem

# pages/serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email
        token['is_staff'] = user.is_staff

        return token


class BookSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.name', read_only=True)

    class Meta:
        model = Book
        fields = ['id', 'title', 'year_published', 'author', 'author_name']
        read_only_fields = ['id']

    def validate_year_published(self, value):
        """Ensure year is reasonable."""
        if value < 1000 or value > 2100:
            raise serializers.ValidationError("Year must be between 1000 and 2100")
        return value

    def validate(self, data):
        """Cross-field validation."""
        # Example: ensure the book wasn't published before the author was born
        if 'author' in data and 'year_published' in data:
            if data['year_published'] < data['author'].birth_year:
                raise serializers.ValidationError(
                    "Book cannot be published before the author was born"
                )
        return data

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = '__all__'



class ReadingListItemSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.title', read_only=True)

    class Meta:
        model = ReadingListItem
        fields = ['id', 'book', 'book_title', 'added_at', 'notes', 'priority']
        read_only_fields = ['id', 'added_at']