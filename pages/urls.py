# ==========================================================================
# pages/urls.py  |  Bookshop — file guide
# ==========================================================================
# The URLconf for the 'pages' app. myproject/urls.py include()s this at the
# root. This project is backend-only, so everything here is API routes --
# there are no HTML page routes.
#
# A DefaultRouter turns each ViewSet into the standard REST URLs:
#
#   /api/authors/            GET list      POST create
#   /api/authors/<pk>/       GET retrieve  PUT  PATCH  DELETE
#   /api/books/              GET list      POST create
#   /api/books/<pk>/         GET retrieve  PUT  PATCH  DELETE
#   /api/reading-list/       the same six, scoped to the logged-in user
#   /api/reading-list/<pk>/
#   /api/                    the browsable API root
#
# basename= is required for BookViewSet and ReadingListViewSet because they
# override get_queryset(), so the router cannot infer the URL names itself.
#
# A ViewSet that is not registered here simply has no URL -- no error, no
# warning, the endpoint just 404s.
# ==========================================================================

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AuthorViewSet, BookViewSet, ReadingListViewSet

router = DefaultRouter()
router.register(r'authors',      AuthorViewSet,      basename='author')
router.register(r'books',        BookViewSet,        basename='book')
router.register(r'reading-list', ReadingListViewSet, basename='readinglistitem')

urlpatterns = [
    path('api/', include(router.urls)),
]
