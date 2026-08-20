# ==========================================================================
# pages/views.py  |  Bookshop — file guide
# ==========================================================================
# All the API endpoints. This project is backend-only: every view here is a
# DRF ViewSet returning JSON, consumed by the React frontend (not built yet).
# There are no HTML page views -- the files in pages/templates/ are kept as
# coursework from weeks 1-3 but nothing renders them.
#
#   CustomTokenObtainPairView   POST /api/token/
#                               username + password -> JWT access/refresh pair,
#                               with username/email/is_staff packed in.
#
#   AuthorViewSet               /api/authors/       full CRUD
#                               IsAuthenticatedOrReadOnly: anyone reads,
#                               only logged-in users write.
#
#   BookViewSet                 /api/books/         full CRUD, same permission
#                               filters: ?title= ?author= ?year= ?category=
#                               perform_create() stamps added_by server-side.
#
#   ReadingListViewSet          /api/reading-list/  IsAuthenticated + IsOwner
#                               row-level: you only ever see your own items.
#
# One ModelViewSet = six actions (list, create, retrieve, update,
# partial_update, destroy). The router in pages/urls.py builds the URLs, and
# the @extend_schema_view decorators are documentation only -- they fill in
# the summaries shown at /api/docs/.
# ==========================================================================

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
)

from .models import Author, Book, ReadingListItem
from .serializers import (
    AuthorSerializer,
    BookSerializer,
    ReadingListItemSerializer,
    CustomTokenObtainPairSerializer,
)
from .permissions import IsOwner


# =========================================================================
# JWT
# =========================================================================

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    POST /api/token/ -- swaps username + password for an access/refresh pair.

    Subclassed only to swap in our serializer, which packs username, email and
    is_staff into the token so the frontend can read them without an extra
    request.

    This must be the ONLY view registered on 'api/token/' in myproject/urls.py.
    Django stops at the first matching pattern, so a stock TokenObtainPairView
    listed above this one would shadow it and the custom claims would silently
    never appear.
    """
    serializer_class = CustomTokenObtainPairSerializer


# =========================================================================
# Author
# =========================================================================

@extend_schema_view(
    list=extend_schema(
        summary="List all authors",
        description="Returns a list of all authors in the system.",
    ),
    create=extend_schema(
        summary="Create a new author",
        description="Adds a new author to the database.",
    ),
    retrieve=extend_schema(
        summary="Get author details",
        description="Returns details for a specific author by ID.",
    ),
    update=extend_schema(
        summary="Replace author",
        description="Completely replaces an author's data.",
    ),
    partial_update=extend_schema(
        summary="Update author fields",
        description="Updates specific fields of an author.",
    ),
    destroy=extend_schema(
        summary="Delete author",
        description="Removes an author from the database.",
    ),
)
class AuthorViewSet(viewsets.ModelViewSet):
    """Full CRUD on Author."""

    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    # Overrides the project-wide IsAuthenticated default in
    # settings.REST_FRAMEWORK: anyone may read, only logged-in users may write.
    permission_classes = [IsAuthenticatedOrReadOnly]


# =========================================================================
# Book
# =========================================================================

@extend_schema_view(
    list=extend_schema(
        summary="List all books",
        description="Returns a list of all books in the bookshop.",
        parameters=[
            OpenApiParameter(
                name='title',
                description='Filter books by title (case-insensitive)',
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name='author',
                description='Filter books by author ID',
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name='year',
                description='Filter books by publication year',
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name='category',
                description='Filter books by category',
                required=False,
                type=str,
            ),
        ],
    ),
    create=extend_schema(
        summary="Add a new book",
        description="Adds a new book to the inventory.",
    ),
    retrieve=extend_schema(
        summary="Get book details",
        description="Returns details of a specific book.",
    ),
    update=extend_schema(
        summary="Replace book",
        description="Completely replaces a book's data.",
    ),
    partial_update=extend_schema(
        summary="Update book fields",
        description="Updates specific fields of a book.",
    ),
    destroy=extend_schema(
        summary="Delete book",
        description="Removes a book from the system.",
    ),
)
class BookViewSet(viewsets.ModelViewSet):
    """Full CRUD on Book, with optional query-string filtering."""

    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """
        Narrow the list by query parameters,
        e.g. /api/books/?title=hob&year=1937

        Every keyword passed to .filter() must be a real model field name. A
        typo is not caught at startup -- it raises FieldError (a 500) the first
        time someone uses that parameter. The field is `year_published`, not
        `year`, which is why the query parameter and the field name differ here.
        """
        queryset = Book.objects.all()

        title = self.request.query_params.get('title')
        if title:
            queryset = queryset.filter(title__icontains=title)

        author_id = self.request.query_params.get('author')
        if author_id:
            queryset = queryset.filter(author_id=author_id)

        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(year_published=year)

        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        return queryset

    def perform_create(self, serializer):
        """
        Record who added the book, taken from the authenticated request rather
        than from the request body -- a client must not be able to claim
        someone else added it. `added_by` is read-only in the serializer for
        the same reason.
        """
        serializer.save(added_by=self.request.user)


# =========================================================================
# Reading list — row-level security
# =========================================================================

class ReadingListViewSet(viewsets.ModelViewSet):
    """
    A user's private reading list.

    Row-level security needs BOTH halves; neither is enough alone:
        get_queryset()  stops other people's rows appearing in the list
        IsOwner         stops someone fetching a row directly by its id
    """

    serializer_class = ReadingListItemSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    
    queryset = ReadingListItem.objects.none()

    def get_queryset(self):
        """Only ever the current user's items."""
        return ReadingListItem.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Set the owner server-side. Never trust the client to send `user` --
        that is how someone writes a row onto somebody else's list.
        """
        serializer.save(user=self.request.user)
