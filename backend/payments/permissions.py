from rest_framework.permissions import BasePermission

ADMIN_ROLES = {"admin", "support"}


class IsAdmin(BasePermission):
    """فقط ادمین و ساپورت"""
    message = "دسترسی محدود به ادمین است."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.role in ADMIN_ROLES or request.user.is_staff)
        )


class IsEditor(BasePermission):
    """فقط ادیتور"""
    message = "فقط ادیتورها به این بخش دسترسی دارند."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "editor"
        )


class IsOwnerOrAdmin(BasePermission):
    """صاحب رکورد یا ادمین"""
    message = "شما مجاز به دسترسی این منبع نیستید."

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role in ADMIN_ROLES or request.user.is_staff:
            return True
        # بررسی owner بر اساس نوع مدل
        owner = getattr(obj, "user", None) or getattr(obj, "editor", None) or getattr(obj, "client", None)
        return owner == request.user
