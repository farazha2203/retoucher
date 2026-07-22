"""
Permissions for refund endpoints.
"""
from rest_framework import permissions


class CanRequestRefund(permissions.BasePermission):
    """Only client or admin can request refund."""
    
    def has_object_permission(self, request, view, obj):
        # obj is the order
        return request.user == obj.client or request.user.is_staff


class CanReviewRefund(permissions.BasePermission):
    """Only admin can review/approve refund."""
    
    def has_permission(self, request, view):
        return request.user.is_staff