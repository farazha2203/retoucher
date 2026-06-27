from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "recipient",
        "actor",
        "notification_type",
        "priority",
        "title",
        "is_read",
        "created_at",
    )
    list_filter = (
        "notification_type",
        "priority",
        "is_read",
        "created_at",
    )
    search_fields = (
        "recipient__username",
        "actor__username",
        "title",
        "message",
    )
    readonly_fields = (
        "created_at",
        "read_at",
    )
    ordering = ("-created_at",)