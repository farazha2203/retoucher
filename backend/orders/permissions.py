from rest_framework import permissions


class IsOrderOwnerOrStaffRole(permissions.BasePermission):
    """
    Allows access to order owner or staff-like roles.
    """

    staff_roles = ("admin", "support", "supervisor")

def has_object_permission(self, request, view, obj):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if user.is_staff:
            return True

        if getattr(user, "role", None) in self.staff_roles:
            return True

        if obj.client_id == user.id:
            return True

        if getattr(obj, "editor_id", None) == user.id:
            return True

        return False


class CanCreateOrder(permissions.BasePermission):
    """
    Only clients can create orders through the main create endpoint.
    Other custom POST actions have their own permission checks.
    """

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if getattr(view, "action", None) == "create":
            return getattr(user, "role", None) == "client"

        return True