from rest_framework import permissions
from .models import ProjectRequest


class IsProjectRequestOwnerOrStaff(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True

        return obj.client_id == request.user.id
    
class IsProjectRequestParticipantOrStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if user.is_staff:
            return True

        if obj.client_id == user.id:
            return True

        editor_profile = getattr(user, "editor_profile", None)

        if editor_profile is None:
            return False

        if obj.target_editor_id == editor_profile.id:
            return True

        if (
            obj.request_type == obj.RequestType.PUBLIC_QUOTE
            and obj.status == obj.Status.OPEN_FOR_QUOTES
            and editor_profile.skills.filter(id=obj.edit_style_id).exists()
        ):
            return True

        if (
            obj.request_type == obj.RequestType.SAMPLE_CHALLENGE
            and obj.status == obj.Status.OPEN_FOR_SAMPLES
            and editor_profile.skills.filter(id=obj.edit_style_id).exists()
        ):
            return True

        return False