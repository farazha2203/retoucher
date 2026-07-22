"""
Dispute resolution models.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class Dispute(models.Model):
    """Formal dispute between client and editor."""

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        UNDER_REVIEW = "under_review", "Under review"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    class Category(models.TextChoices):
        QUALITY = "quality", "Quality issue"
        SCOPE = "scope", "Scope change"
        DEADLINE = "deadline", "Deadline missed"
        PAYMENT = "payment", "Payment dispute"
        OTHER = "other", "Other"

    class Resolution(models.TextChoices):
        FAVORS_CLIENT = "favors_client", "Favors client (full refund)"
        FAVORS_EDITOR = "favors_editor", "Favors editor (no refund)"
        COMPROMISE = "compromise", "Compromise (partial refund)"
        DISMISSED = "dismissed", "Dismissed"

    # Links
    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='dispute',
    )
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='disputes_initiated',
    )

    # Details
    category = models.CharField(max_length=20, choices=Category.choices)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)

    # Resolution
    resolution = models.CharField(
        max_length=20, choices=Resolution.choices,
        null=True, blank=True,
    )
    resolution_note = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='disputes_resolved',
    )
    refund_amount = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Refund amount if resolution involves partial/full refund",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Response deadline
    response_deadline = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = "Dispute"
        verbose_name_plural = "Disputes"

    def __str__(self):
        return f"Dispute for Order {self.order_id} - {self.status}"

    def resolve(self, resolution, resolved_by, note="", refund_amount=None):
        """Resolve the dispute."""
        self.resolution = resolution
        self.resolved_by = resolved_by
        self.resolution_note = note
        self.status = self.Status.RESOLVED
        self.resolved_at = timezone.now()
        if refund_amount is not None:
            self.refund_amount = refund_amount
        self.save()


class DisputeMessage(models.Model):
    """Messages/comments in a dispute thread."""

    dispute = models.ForeignKey(
        Dispute,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='dispute_messages',
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_admin_note = models.BooleanField(
        default=False,
        help_text="If True, only visible to admin",
    )

    class Meta:
        ordering = ('created_at',)

    def __str__(self):
        return f"Message by {self.sender_id} in Dispute {self.dispute_id}"


class DisputeEvidence(models.Model):
    """Evidence files uploaded for a dispute."""

    dispute = models.ForeignKey(
        Dispute,
        on_delete=models.CASCADE,
        related_name='evidence',
    )
    file = models.FileField(upload_to='dispute_evidence/')
    description = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='dispute_evidence',
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('uploaded_at',)

    def __str__(self):
        return f"Evidence for Dispute {self.dispute_id}"