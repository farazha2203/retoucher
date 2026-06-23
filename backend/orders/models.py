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
        CLIENT_REVISION_REQUESTED = "client_revision_requested", "Client Revision Requested"
        COMPLETED = "completed", "Completed"
        SETTLEMENT_PENDING = "settlement_pending", "Settlement Pending"

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

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.source} rating {self.score}/10 for order #{self.order_id}"