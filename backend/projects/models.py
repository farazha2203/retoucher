from django.conf import settings
from django.db import models

from accounts.models import EditorProfile
from catalog.models import EditPackage, EditStyle


class ProjectRequest(models.Model):
    class RequestType(models.TextChoices):
        DIRECT_EDITOR = "direct_editor", "Direct editor"
        PUBLIC_QUOTE = "public_quote", "Public quote"
        SAMPLE_CHALLENGE = "sample_challenge", "Sample challenge"
        MANAGED_ORDER = "managed_order", "Managed order"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        OPEN_FOR_QUOTES = "open_for_quotes", "Open for quotes"
        OPEN_FOR_SAMPLES = "open_for_samples", "Open for samples"
        WAITING_FOR_EDITOR = "waiting_for_editor", "Waiting for editor"
        UNDER_REVIEW = "under_review", "Under review"
        EDITOR_SELECTED = "editor_selected", "Editor selected"
        CONVERTED_TO_ORDER = "converted_to_order", "Converted to order"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_requests",
    )

    request_type = models.CharField(
        max_length=30,
        choices=RequestType.choices,
        default=RequestType.MANAGED_ORDER,
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)

    edit_style = models.ForeignKey(
        EditStyle,
        on_delete=models.PROTECT,
        related_name="project_requests",
    )
    package = models.ForeignKey(
        EditPackage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_requests",
    )

    target_editor = models.ForeignKey(
        EditorProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="targeted_project_requests",
        help_text="Used for direct editor requests.",
    )

    budget_min = models.PositiveIntegerField(default=0)
    budget_max = models.PositiveIntegerField(default=0)
    preferred_deadline = models.DateTimeField(null=True, blank=True)

    image_count = models.PositiveIntegerField(default=0)

    client_note = models.TextField(blank=True)
    support_note = models.TextField(blank=True)

    converted_order = models.OneToOneField(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_project_request",
    )

    submitted_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Project request"
        verbose_name_plural = "Project requests"

    def __str__(self):
        return f"{self.title} - {self.client}"


class ProjectRequestImage(models.Model):
    project_request = models.ForeignKey(
        ProjectRequest,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="project_requests/originals/")
    caption = models.CharField(max_length=180, blank=True)
    is_sample_image = models.BooleanField(
        default=False,
        help_text="Used for sample challenge requests.",
    )
    sort_order = models.PositiveIntegerField(default=0)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "uploaded_at"]
        verbose_name = "Project request image"
        verbose_name_plural = "Project request images"

    def __str__(self):
        return f"Image for {self.project_request_id}"