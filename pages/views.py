# pages/views.py

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
)

from .models import Author, Book, ReadingListItem
from .serializers import AuthorSerializer, BookSerializer, ReadingListItemSerializer

# pages/views.py
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from .permissions import IsOwner
from django.shortcuts import render




# Custom Token Claims. You can add extra data to your tokens by creating a custom serializer:


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer



# =========================
# Author ViewSet
# =========================

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
    """
    ViewSet for managing authors.

    Provides full CRUD functionality.
    """
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


# =========================
# Book ViewSet
# =========================

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
    """
    ViewSet for managing books.

    Provides:
    - list
    - create
    - retrieve
    - update
    - partial_update
    - destroy
    """

    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """
        Optionally filter books based on query parameters.
        """

        queryset = Book.objects.all()

        # Filter by title
        title = self.request.query_params.get('title')
        if title:
            queryset = queryset.filter(title__icontains=title)

        # Filter by author
        author_id = self.request.query_params.get('author')
        if author_id:
            queryset = queryset.filter(author_id=author_id)

        # Filter by year
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(year=year)

        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        return queryset


class ReadingListViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user's personal reading list.

    Users can only see and modify their own reading list items.
    """
    serializer_class = ReadingListItemSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        """Filter to only show the current user's reading list."""
        return ReadingListItem.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Automatically set the user when creating a reading list item."""
        serializer.save(user=self.request.user)