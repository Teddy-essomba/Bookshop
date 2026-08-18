# ==========================================================================
# pages/serializers.py  |  Bookshop — file guide
# ==========================================================================
# Serializers are the API's version of forms. They render model instances as
# JSON on the way out, and validate + build model instances on the way in.
#
# Mapping to pages/forms.py:
#     clean_<field>()  ->  validate_<field>()
#     clean()          ->  validate()
#     form.save()      ->  serializer.save()
# One gotcha: the ValidationError here is serializers.ValidationError, NOT
# django.core.exceptions.ValidationError. Different class, different module.
#
#   CustomTokenObtainPairSerializer  adds username/email/is_staff to the JWT
#   AuthorSerializer                 Author, all four fields listed explicitly
#   BookSerializer                   Book + a read-only author_name
#   ReadingListItemSerializer        one saved book + a read-only book_title
# ==========================================================================

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Author, Book, ReadingListItem


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Puts extra claims inside the access token.

    By default the token only carries the user id, so the frontend would need
    a second request just to display a username. These claims travel with the
    token instead. Wired up by CustomTokenObtainPairView in views.py.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Custom claims
        token['username'] = user.username
        token['email'] = user.email
        token['is_staff'] = user.is_staff

        return token


class AuthorSerializer(serializers.ModelSerializer):
    """Author, read and write."""

    class Meta:
        model = Author
        # Fields are listed explicitly rather than '__all__'. With '__all__',
        # any field added to the model later becomes client-writable by
        # accident -- including ones that shouldn't be.
        fields = ['id', 'name', 'birth_year', 'country']
        read_only_fields = ['id']


class BookSerializer(serializers.ModelSerializer):
    """Book, read and write."""

    # Pulled through the ForeignKey so clients get the author's name without a
    # second request. Read-only: clients still POST `author` as an id.
    author_name = serializers.CharField(source='author.name', read_only=True)

    # Who added the book. Read-only here and set server-side in
    # BookViewSet.perform_create() -- never let a client claim authorship.
    added_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'year_published',
            'author', 'author_name',
            'category', 'added_by',
        ]
        read_only_fields = ['id', 'added_by']

    def validate_year_published(self, value):
        """Field-level check: one field, in isolation. Must return the value."""
        if value < 1000 or value > 2100:
            raise serializers.ValidationError("Year must be between 1000 and 2100")
        return value

    def validate(self, data):
        """
        Cross-field check: runs after the per-field ones.

        Uses .get() rather than [] because on a PATCH only the changed fields
        are present -- assuming a key exists is how this blows up on partial
        updates.
        """
        author = data.get('author') or getattr(self.instance, 'author', None)
        year = data.get('year_published') or getattr(self.instance, 'year_published', None)

        if author is not None and year is not None:
            if year < author.birth_year:
                raise serializers.ValidationError(
                    "Book cannot be published before the author was born"
                )
        return data


class ReadingListItemSerializer(serializers.ModelSerializer):
    """
    One book on a user's list.

    `user` is deliberately absent from fields -- ReadingListViewSet sets it
    from request.user, so a client cannot write onto someone else's list.
    """

    book_title = serializers.CharField(source='book.title', read_only=True)

    class Meta:
        model = ReadingListItem
        fields = ['id', 'book', 'book_title', 'added_at', 'notes', 'priority']
        read_only_fields = ['id', 'added_at']
