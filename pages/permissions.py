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