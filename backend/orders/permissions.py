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

        return obj.client_id == user.id


class CanCreateOrder(permissions.BasePermission):
    """
    Only clients can create orders.
    Staff can create only if needed later, but currently blocked.
    """

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if request.method == "POST":
            return getattr(user, "role", None) == "client"

        return True