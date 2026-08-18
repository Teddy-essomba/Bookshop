# ==========================================================================
# pages/permissions.py  |  Bookshop — file guide
# ==========================================================================
# Custom DRF permission classes - object-level ("row-level") authorization.
#
# Django's built-in permissions are per MODEL ("can edit books"), not per ROW
# ("can edit THIS book"), so ownership rules get written by hand here.
#
#   IsOwner.has_object_permission()  ->  obj.user == request.user
#
# Used by ReadingListViewSet alongside IsAuthenticated. Note it takes both:
# IsOwner guards access to a single object fetched by id, while the viewset's
# get_queryset() is what stops other people's rows appearing in the list. You
# need both halves - one without the other leaks data.
#
# Assumes the model has a `user` field, which is why it fits ReadingListItem but
# not Book (Book uses `added_by`).
# ==========================================================================

# pages/permissions.py
from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to access it.

    Assumes the model has a 'user' field pointing to the owner.
    """

    def has_object_permission(self, request, view, obj):
        # Check if the object's user field matches the requesting user
        return obj.user == request.user