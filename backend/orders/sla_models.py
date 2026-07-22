"""
SLA and delivery penalty models.
"""
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.conf import settings
from django.utils import timezone


class DeliveryPenalty(models.Model):
    """Penalty applied when editor delivers late."""

    class PenaltyType(models.TextChoices):
        LATE_DELIVERY = "late_delivery", "Late delivery"
        QUALITY_ISSUE = "quality_issue", "Quality issue"
        MANUAL = "manual", "Manual penalty"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPLIED = "applied", "Applied"
        WAIVED = "waived", "Waived"
        DISPUTED = "disputed", "Disputed"

    # Links
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='penalties',
    )
    editor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='penalties_received',
    )

    # Penalty details
    penalty_type = models.CharField(
        max_length=30,
        choices=PenaltyType.choices,
        default=PenaltyType.LATE_DELIVERY,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    # Amounts
    order_amount = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        help_text="Original order amount (agreed_price)",
    )
    penalty_amount = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        help_text="Penalty amount deducted from editor",
    )
    penalty_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Penalty as percentage of order amount",
    )

    # SLA details
    deadline = models.DateTimeField(
        help_text="Original order deadline",
    )
    delivered_at = models.DateTimeField(
        null=True, blank=True,
        help_text="When order was actually delivered",
    )
    days_late = models.PositiveIntegerField(
        default=0,
        help_text="Number of days late",
    )

    # Reason
    reason = models.TextField(blank=True)
    admin_note = models.TextField(blank=True)

    # Reviewed by
    applied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='penalties_applied',
    )
    waived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='penalties_waived',
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    applied_at = models.DateTimeField(null=True, blank=True)
    waived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = "Delivery Penalty"
        verbose_name_plural = "Delivery Penalties"

    def __str__(self):
        return f"Penalty for Order {self.order_id} - {self.penalty_amount} tomans"

    @transaction.atomic
    def apply(self, applied_by=None, note=""):
        """Apply a pending penalty and atomically deduct editor earnings."""
        from payments.services import deduct_editor_penalty

        locked = type(self).objects.select_for_update().select_related(
            "editor", "order"
        ).get(pk=self.pk)

        if locked.status != self.Status.PENDING:
            raise ValidationError(
                f"Cannot apply penalty with status: {locked.status}"
            )

        wallet_transaction = deduct_editor_penalty(
            editor=locked.editor,
            amount=locked.penalty_amount,
            order=locked.order,
            created_by=applied_by,
            description=(
                f"SLA penalty for late delivery on order #{locked.order_id}"
            ),
            meta={
                "delivery_penalty_id": locked.pk,
                "penalty_type": locked.penalty_type,
                "days_late": locked.days_late,
            },
        )

        locked.status = self.Status.APPLIED
        locked.applied_by = applied_by
        locked.applied_at = timezone.now()
        locked.admin_note = (note or "").strip()
        locked.save(
            update_fields=[
                "status",
                "applied_by",
                "applied_at",
                "admin_note",
            ]
        )

        self.refresh_from_db()
        return wallet_transaction

    @transaction.atomic
    def waive(self, waived_by=None, note=""):
        """Waive a pending penalty before any wallet deduction occurs."""
        locked = type(self).objects.select_for_update().get(pk=self.pk)

        if locked.status != self.Status.PENDING:
            raise ValidationError(
                "Only pending penalties can be waived. Applied penalties require "
                "an explicit financial reversal workflow."
            )

        locked.status = self.Status.WAIVED
        locked.waived_by = waived_by
        locked.waived_at = timezone.now()
        locked.admin_note = (note or "").strip()
        locked.save(
            update_fields=[
                "status",
                "waived_by",
                "waived_at",
                "admin_note",
            ]
        )

        self.refresh_from_db()


class SLAConfig(models.Model):
    """SLA configuration - penalty rates per day late."""

    # Penalty per day late (percentage of order value)
    penalty_percent_per_day = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=2.00,
        help_text="Penalty percentage per day late (e.g. 2.00 = 2% per day)",
    )

    # Max total penalty
    max_penalty_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20.00,
        help_text="Maximum total penalty percentage (e.g. 20 = max 20% of order)",
    )

    # Grace period
    grace_period_hours = models.PositiveIntegerField(
        default=2,
        help_text="Hours of grace period before penalty starts",
    )

    # Active
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "SLA Configuration"
        verbose_name_plural = "SLA Configurations"

    def __str__(self):
        return f"SLA Config: {self.penalty_percent_per_day}%/day, max {self.max_penalty_percent}%"

    @classmethod
    def get_active(cls):
        """Get active SLA config or create default."""
        config = cls.objects.filter(is_active=True).first()
        if not config:
            config = cls.objects.create()
        return config

