from django.contrib import admin

from .models import (
    Conversation,
    ConversationParticipant,
    FileDownloadLog,
    ManagedFile,
    Message,
    MessageAttachment,
    SystemAuditLog,
)


class ConversationParticipantInline(admin.TabularInline):
    model = ConversationParticipant
    extra = 0


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "kind", "order", "project_request", "last_message_at", "is_archived")
    list_filter = ("kind", "is_archived")
    search_fields = ("title", "order__title", "project_request__title")
    inlines = (ConversationParticipantInline,)


class MessageAttachmentInline(admin.TabularInline):
    model = MessageAttachment
    extra = 0


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "sender", "message_type", "created_at", "deleted_at")
    list_filter = ("message_type", "created_at")
    search_fields = ("body", "sender__username", "conversation__title")
    inlines = (MessageAttachmentInline,)


@admin.register(ManagedFile)
class ManagedFileAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "category", "order", "project_request", "uploaded_by", "size_bytes", "download_count", "created_at")
    list_filter = ("category", "is_private", "created_at")
    search_fields = ("title", "description", "uploaded_by__username")


@admin.register(FileDownloadLog)
class FileDownloadLogAdmin(admin.ModelAdmin):
    list_display = ("managed_file", "user", "ip_address", "downloaded_at")
    list_filter = ("downloaded_at",)
    readonly_fields = ("managed_file", "user", "ip_address", "user_agent", "downloaded_at")


@admin.register(SystemAuditLog)
class SystemAuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "level", "action", "actor", "method", "path", "status_code", "ip_address")
    list_filter = ("level", "action", "method", "status_code", "created_at")
    search_fields = ("action", "message", "path", "actor__username", "request_id")
    readonly_fields = (
        "actor", "action", "level", "method", "path", "status_code",
        "target_type", "target_id", "message", "metadata", "ip_address",
        "user_agent", "request_id", "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
