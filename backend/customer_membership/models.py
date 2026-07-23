from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class CustomerTier(models.Model):
    class Code(models.TextChoices):
        NORMAL = "normal", "مشتری عادی"
        STUDIO = "studio", "آتلیه‌دار"
        STUDIO_VIP = "studio_vip", "آتلیه‌دار VIP"

    code = models.CharField(max_length=30, choices=Code.choices, unique=True)
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    priority_level = models.PositiveSmallIntegerField(default=0)
    badge_title = models.CharField(max_length=80, blank=True)
    badge_color = models.CharField(max_length=20, default="#9B85E8")
    monthly_price = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    annual_price = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    advertising_enabled = models.BooleanField(default=False)
    logo_enabled = models.BooleanField(default=False)
    featured_listing_enabled = models.BooleanField(default=False)
    is_purchasable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "id")

    def __str__(self):
        return self.title


class CustomerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer_membership_profile")
    tier = models.ForeignKey(CustomerTier, on_delete=models.PROTECT, related_name="customers", null=True, blank=True)
    national_id = models.CharField(max_length=10, blank=True, db_index=True)
    birth_date = models.DateField(null=True, blank=True)
    landline = models.CharField(max_length=20, blank=True)
    occupation = models.CharField(max_length=120, blank=True)
    province = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    profile_completed = models.BooleanField(default=False)
    admin_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def active_subscription(self):
        now = timezone.now()
        return self.subscriptions.filter(status=CustomerSubscription.Status.ACTIVE, starts_at__lte=now, ends_at__gt=now).select_related("tier").order_by("-ends_at").first()

    @property
    def effective_tier(self):
        subscription = self.active_subscription
        return subscription.tier if subscription else self.tier

    @property
    def effective_discount_percent(self):
        tier = self.effective_tier
        return tier.discount_percent if tier else Decimal("0")

    @property
    def effective_priority_level(self):
        tier = self.effective_tier
        return tier.priority_level if tier else 0

    def __str__(self):
        return f"{self.user} - {self.effective_tier or 'normal'}"


class StudioProfile(models.Model):
    customer = models.OneToOneField(CustomerProfile, on_delete=models.CASCADE, related_name="studio")
    studio_name = models.CharField(max_length=180)
    legal_name = models.CharField(max_length=180, blank=True)
    manager_name = models.CharField(max_length=150, blank=True)
    registration_number = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    secondary_phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    instagram = models.CharField(max_length=120, blank=True)
    activity_fields = models.TextField(blank=True)
    province = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    logo = models.ImageField(upload_to="studios/logos/", null=True, blank=True)
    description = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    advertising_enabled = models.BooleanField(default=False)
    featured_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.studio_name


class CustomerSubscription(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار پرداخت"
        ACTIVE = "active", "فعال"
        EXPIRED = "expired", "منقضی"
        CANCELLED = "cancelled", "لغوشده"

    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name="subscriptions")
    tier = models.ForeignKey(CustomerTier, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    purchased_amount = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    auto_renew = models.BooleanField(default=False)
    payment_reference = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)


class PerformanceCommissionRule(models.Model):
    title = models.CharField(max_length=120)
    min_rating = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    min_likes = models.PositiveIntegerField(default=0)
    site_commission_percent = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    supervisor_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    expert_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("-min_rating", "-min_likes", "sort_order")

    def __str__(self):
        return self.title


class OrderPricingSnapshot(models.Model):
    order = models.OneToOneField("orders.Order", on_delete=models.CASCADE, related_name="membership_pricing_snapshot")
    base_price = models.DecimalField(max_digits=14, decimal_places=0)
    customer_discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    customer_discount_amount = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    final_price = models.DecimalField(max_digits=14, decimal_places=0)
    site_commission_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    site_commission_amount = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    supervisor_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    supervisor_amount = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    expert_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    expert_amount = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    editor_earning = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    rule = models.ForeignKey(PerformanceCommissionRule, on_delete=models.SET_NULL, null=True, blank=True)
    calculator_version = models.CharField(max_length=30, default="5.4.0")
    calculated_at = models.DateTimeField(auto_now=True)
