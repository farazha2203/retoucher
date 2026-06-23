from django.conf import settings
from django.db import models


class Order(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        IN_REVIEW = "in_review", "In Review"
        ASSIGNED = "assigned", "Assigned"
        IN_PROGRESS = "in_progress", "In Progress"
        DELIVERED = "delivered", "Delivered"
        REVISION_REQUESTED = "revision_requested", "Revision Requested"
        CANCELLED = "cancelled", "Cancelled"
        CLIENT_REVIEW = "client_review", "Client Review"
        REVISION_REQUIRED = "revision_required", "Revision Required"
        CLIENT_REVISION_REQUESTED = (
            "client_revision_requested",
            "Client Revision Requested",
        )
        COMPLETED = "completed", "Completed"
        SETTLEMENT_PENDING = "settlement_pending", "Settlement Pending"
        PAID = "paid", "Paid"
        CLOSED = "closed", "Closed"

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
    )

    editor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_orders",
        blank=True,
        null=True,
    )

    settlement_started_at = models.DateTimeField(
        blank=True,
        null=True,
    )
    paid_at = models.DateTimeField(
        blank=True,
        null=True,
    )
    closed_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    supervisor_approved_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    client_approved_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    title = models.CharField(
        max_length=255,
    )
    description = models.TextField(
        blank=True,
    )
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    revision_count = models.PositiveSmallIntegerField(
        default=0,
    )

    supervisor_approved_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    client_approved_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    deadline = models.DateTimeField(
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.title} - {self.client.username}"


class OrderDelivery(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="deliveries",
    )
    file = models.FileField(
        upload_to="orders/deliveries/",
    )
    note = models.TextField(
        blank=True,
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="order_deliveries",
        blank=True,
        null=True,
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ("-uploaded_at",)

    def __str__(self):
        return f"Delivery for order #{self.order_id}"


class OrderRevision(models.Model):
    class Source(models.TextChoices):
        SUPERVISOR = "supervisor", "Supervisor"
        CLIENT = "client", "Client"

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="revisions",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="order_revisions",
        blank=True,
        null=True,
    )
    source = models.CharField(
        max_length=32,
        choices=Source.choices,
    )
    note = models.TextField()
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.source} revision for order #{self.order_id}"


class OrderImage(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(
        upload_to="orders/originals/",
    )
    note = models.CharField(
        max_length=255,
        blank=True,
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ("uploaded_at",)

    def __str__(self):
        return f"Image for order #{self.order_id}"


class OrderRating(models.Model):
    class Source(models.TextChoices):
        SUPERVISOR = "supervisor", "Supervisor"
        CLIENT = "client", "Client"

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="ratings",
    )
    rated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="order_ratings",
        blank=True,
        null=True,
    )
    source = models.CharField(
        max_length=32,
        choices=Source.choices,
    )
    score = models.PositiveSmallIntegerField()
    comment = models.TextField(
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.source} rating {self.score}/10 for order #{self.order_id}"


class OrderComment(models.Model):
    class TargetType(models.TextChoices):
        ORDER = "order", "Order"
        IMAGE = "image", "Image"
        DELIVERY = "delivery", "Delivery"
        REVISION = "revision", "Revision"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        RESOLVED = "resolved", "Resolved"
        APPROVED = "approved", "Approved"
        DELETED = "deleted", "Deleted"

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="order_comments",
        blank=True,
        null=True,
    )
    target_type = models.CharField(
        max_length=32,
        choices=TargetType.choices,
        default=TargetType.ORDER,
    )
    image = models.ForeignKey(
        OrderImage,
        on_delete=models.CASCADE,
        related_name="comments",
        blank=True,
        null=True,
    )
    delivery = models.ForeignKey(
        OrderDelivery,
        on_delete=models.CASCADE,
        related_name="comments",
        blank=True,
        null=True,
    )
    revision = models.ForeignKey(
        OrderRevision,
        on_delete=models.CASCADE,
        related_name="comments",
        blank=True,
        null=True,
    )
    text = models.TextField()

    # Optional coordinates for future image annotation.
    x = models.FloatField(
        blank=True,
        null=True,
    )
    y = models.FloatField(
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    is_edited = models.BooleanField(
        default=False,
    )
    edited_at = models.DateTimeField(
        blank=True,
        null=True,
    )
    deleted_at = models.DateTimeField(
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return f"Comment #{self.id} on order #{self.order_id}"
    
class OrderStatusHistory(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="status_history",
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="order_status_changes",
        blank=True,
        null=True,
    )
    from_status = models.CharField(
        max_length=32,
        blank=True,
    )
    to_status = models.CharField(
        max_length=32,
    )
    note = models.TextField(
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return f"Order #{self.order_id}: {self.from_status} -> {self.to_status}"
    
class OrderActivityLog(models.Model):
    class ActivityType(models.TextChoices):
        ORDER_SUBMITTED = "order_submitted", "Order Submitted"
        REVIEW_STARTED = "review_started", "Review Started"
        EDITOR_ASSIGNED = "editor_assigned", "Editor Assigned"
        WORK_STARTED = "work_started", "Work Started"
        DELIVERY_UPLOADED = "delivery_uploaded", "Delivery Uploaded"
        SUPERVISOR_APPROVED = "supervisor_approved", "Supervisor Approved"
        SUPERVISOR_REVISION_REQUESTED = "supervisor_revision_requested", "Supervisor Revision Requested"
        EDITOR_REVISION_STARTED = "editor_revision_started", "Editor Revision Started"
        CLIENT_APPROVED = "client_approved", "Client Approved"
        CLIENT_REVISION_REQUESTED = "client_revision_requested", "Client Revision Requested"
        SUPERVISOR_ACCEPTED_CLIENT_REVISION = "supervisor_accepted_client_revision", "Supervisor Accepted Client Revision"
        SUPERVISOR_REJECTED_CLIENT_REVISION = "supervisor_rejected_client_revision", "Supervisor Rejected Client Revision"
        COMMENT_CREATED = "comment_created", "Comment Created"
        COMMENT_UPDATED = "comment_updated", "Comment Updated"
        COMMENT_DELETED = "comment_deleted", "Comment Deleted"
        RATING_CREATED = "rating_created", "Rating Created"
        RATING_UPDATED = "rating_updated", "Rating Updated"
        SETTLEMENT_STARTED = "settlement_started", "Settlement Started"
        PAYMENT_RECORDED = "payment_recorded", "Payment Recorded"
        ORDER_CLOSED = "order_closed", "Order Closed"

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="activity_logs",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="order_activity_logs",
        null=True,
        blank=True,
    )
    activity_type = models.CharField(
        max_length=64,
        choices=ActivityType.choices,
    )
    message = models.TextField(
        blank=True,
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return f"Order #{self.order_id} - {self.activity_type}"
