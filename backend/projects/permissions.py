from rest_framework import permissions


class IsProjectRequestOwnerOrStaff(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True

        return obj.client_id == request.user.id