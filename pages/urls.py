# ==========================================================================
# pages/urls.py  |  Bookshop — file guide
# ==========================================================================
# The URLconf for the 'pages' app. myproject/urls.py include()s this at the root,
# so everything below is relative to '/'.
#
# A DefaultRouter takes each ViewSet and generates the standard REST URLs:
#
#     /api/authors/        GET list      POST create
#     /api/authors/<pk>/   GET retrieve  PUT update  PATCH partial  DELETE destroy
#     /api/books/          GET list      POST create
#     /api/books/<pk>/     GET retrieve  PUT update  PATCH partial  DELETE destroy
#     /api/                the browsable API root
#
# basename=... is required because BookViewSet/ReadingListViewSet override
# get_queryset(), so the router can't infer the URL names by itself.
#


# pages/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuthorViewSet, BookViewSet
from . import views

router = DefaultRouter()
router.register(r'authors', AuthorViewSet, basename='author')
router.register(r'books', BookViewSet, basename='book')

urlpatterns = [
    path('api/', include(router.urls)),
]
