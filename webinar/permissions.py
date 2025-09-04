from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "admin"


class IsHostUser(permissions.BasePermission):
    """
    Custom permission to only allow host users.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "host"


class IsAdminOrHostOwner(permissions.BasePermission):
    """
    Custom permission to allow admin users or host users who own the webinar.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ["admin", "host"]

    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True
        if request.user.role == "host":
            return obj.host == request.user
        return False


class IsAttendeeUser(permissions.BasePermission):
    """
    Custom permission to only allow attendee users.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "attendee"
