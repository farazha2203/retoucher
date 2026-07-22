"""
Refund models for handling order refunds and returns.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class Refund(models.Model):
    """Refund request for an order."""
    
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        UNDER_REVIEW = "under_review", "Under review"
        APPROVED = "approved", "Approved"
        PARTIAL = "partial", "Partial refund"
        REJECTED = "rejected", "Rejected"
        PROCESSED = "processed", "Processed"
        FAILED = "failed", "Failed"
    
    class Reason(models.TextChoices):
        DISPUTE = "dispute", "Quality dispute"
        CANCELLATION = "cancellation", "Order cancellation"
        QUALITY_ISSUE = "quality_issue", "Quality issue"
        LATE_DELIVERY = "late_delivery", "Late delivery"
        OTHER = "other", "Other"
    
    # Links
    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='refund',
    )
    
    # Refund details
    reason = models.CharField(
        max_length=30,
        choices=Reason.choices,
        default=Reason.DISPUTE,
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.REQUESTED,
    )
    
    # Amount (in tomans)
    requested_amount = models.PositiveIntegerField()
    approved_amount = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    
    # Requestor
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='refunds_requested',
    )
    
    # Admin review
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='refunds_reviewed',
    )
    
    # Description
    description = models.TextField(blank=True)
    admin_note = models.TextField(blank=True)
    
    # Dates
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Wallet transaction
    wallet_transaction = models.OneToOneField(
        'payments.Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='refund',
    )
    
    class Meta:
        ordering = ('-requested_at',)
        verbose_name = "Refund"
        verbose_name_plural = "Refunds"
    
    def __str__(self):
        return f"Refund for Order {self.order_id} - {self.status}"
    
    @property
    @property
    def can_request_refund(self):
        """Check if refund can be requested for this order."""
        if self.order.status not in ['completed', 'closed', 'paid']:
            return False
        
        # Only within 7 days of closing/payment
        reference_date = self.order.closed_at or self.order.paid_at
        if not reference_date:
            return False
        
        days_elapsed = (timezone.now() - reference_date).days
        if days_elapsed > 7:
            return False
        
        return True
    
    def approve(self, amount=None, reviewed_by=None, note=""):
        """Approve refund."""
        self.status = self.Status.APPROVED
        self.approved_amount = amount or self.requested_amount
        self.reviewed_by = reviewed_by
        self.admin_note = note
        self.reviewed_at = timezone.now()
        self.save()
    
    def reject(self, reviewed_by=None, note=""):
        """Reject refund."""
        self.status = self.Status.REJECTED
        self.reviewed_by = reviewed_by
        self.admin_note = note
        self.reviewed_at = timezone.now()
        self.save()


class RefundEvidence(models.Model):
    """Evidence files for refund requests."""
    
    refund = models.ForeignKey(
        Refund,
        on_delete=models.CASCADE,
        related_name='evidence',
    )
    
    file = models.FileField(upload_to='refund_evidence/')
    description = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ('uploaded_at',)
        verbose_name = "Refund Evidence"
        verbose_name_plural = "Refund Evidence"
    
    def __str__(self):
        return f"Evidence for Refund {self.refund_id}"