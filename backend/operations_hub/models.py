from pathlib import Path

from django.conf import settings
from django.db import models
from django.utils import timezone


class Conversation(models.Model):
    class Kind(models.TextChoices):
        ORDER = "order", "سفارش"
        PROJECT = "project", "پروژه"
        SUPPORT = "support", "پشتیبانی"
        INTERNAL = "internal", "داخلی"

    title = models.CharField(max_length=200)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.SUPPORT)
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="panel_conversations",
        null=True,
        blank=True,
    )
    project_request = models.ForeignKey(
        "projects.ProjectRequest",
        on_delete=models.CASCADE,
        related_name="panel_conversations",
        null=True,
        blank=True,
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="ConversationParticipant",
        related_name="panel_conversations",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_panel_conversations",
        null=True,
        blank=True,
    )
    is_archived = models.BooleanField(default=False)
    last_message_at = models.DateTimeField(default=timezone.now, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-last_message_at", "-id")
        indexes = [
            models.Index(fields=["kind", "is_archived"]),
            models.Index(fields=["last_message_at"]),
        ]

    def __str__(self):
        return self.title


class ConversationParticipant(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="participant_links",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversation_participations",
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_at = models.DateTimeField(null=True, blank=True)
    is_muted = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "user"],
                name="unique_conversation_participant",
            )
        ]
        indexes = [
            models.Index(fields=["user", "last_read_at"]),
        ]

    def __str__(self):
        return f"{self.conversation_id}:{self.user_id}"


class Message(models.Model):
    class Type(models.TextChoices):
        TEXT = "text", "متن"
        FILE = "file", "فایل"
        SYSTEM = "system", "سیستمی"

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="panel_messages",
        null=True,
        blank=True,
    )
    reply_to = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="replies",
        null=True,
        blank=True,
    )
    message_type = models.CharField(max_length=16, choices=Type.choices, default=Type.TEXT)
    body = models.TextField(blank=True)
    is_edited = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("created_at", "id")
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
            models.Index(fields=["sender", "created_at"]),
        ]

    def __str__(self):
        return f"message:{self.pk or 'new'}"


class MessageAttachment(models.Model):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file = models.FileField(upload_to="panel/chat/%Y/%m/")
    original_name = models.CharField(max_length=255, blank=True)
    mime_type = models.CharField(max_length=120, blank=True)
    size_bytes = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def display_name(self):
        return self.original_name or Path(self.file.name).name

    def __str__(self):
        return self.display_name


class ManagedFile(models.Model):
    class Category(models.TextChoices):
        INPUT = "input", "فایل ورودی"
        DELIVERY = "delivery", "خروجی"
        REFERENCE = "reference", "مرجع"
        CONTRACT = "contract", "قرارداد"
        GENERAL = "general", "عمومی"

    file = models.FileField(upload_to="panel/files/%Y/%m/")
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.GENERAL)
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="managed_files",
        null=True,
        blank=True,
    )
    project_request = models.ForeignKey(
        "projects.ProjectRequest",
        on_delete=models.CASCADE,
        related_name="managed_files",
        null=True,
        blank=True,
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="uploaded_managed_files",
        null=True,
        blank=True,
    )
    description = models.TextField(blank=True)
    mime_type = models.CharField(max_length=120, blank=True)
    size_bytes = models.PositiveBigIntegerField(default=0)
    version = models.PositiveIntegerField(default=1)
    is_private = models.BooleanField(default=True)
    download_count = models.PositiveIntegerField(default=0)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["order", "category"]),
            models.Index(fields=["project_request", "category"]),
            models.Index(fields=["uploaded_by", "created_at"]),
        ]

    @property
    def filename(self):
        return Path(self.file.name).name

    def __str__(self):
        return self.title


class FileDownloadLog(models.Model):
    managed_file = models.ForeignKey(
        ManagedFile,
        on_delete=models.CASCADE,
        related_name="download_logs",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="file_download_logs",
        null=True,
        blank=True,
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    downloaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-downloaded_at",)
        indexes = [
            models.Index(fields=["managed_file", "downloaded_at"]),
            models.Index(fields=["user", "downloaded_at"]),
        ]


class SystemAuditLog(models.Model):
    class Level(models.TextChoices):
        INFO = "info", "اطلاعات"
        WARNING = "warning", "هشدار"
        ERROR = "error", "خطا"
        SECURITY = "security", "امنیتی"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="system_audit_logs",
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=100, db_index=True)
    level = models.CharField(max_length=16, choices=Level.choices, default=Level.INFO)
    method = models.CharField(max_length=12, blank=True)
    path = models.CharField(max_length=500, blank=True)
    status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    target_type = models.CharField(max_length=100, blank=True)
    target_id = models.CharField(max_length=100, blank=True)
    message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_id = models.CharField(max_length=64, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["actor", "created_at"]),
            models.Index(fields=["action", "created_at"]),
            models.Index(fields=["level", "created_at"]),
        ]

    def __str__(self):
        return f"{self.action} @ {self.created_at}"
