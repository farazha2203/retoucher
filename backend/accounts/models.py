from django.contrib.auth.models import AbstractUser
from django.db import models
from catalog.models import EditStyle
from django.conf import settings


class User(AbstractUser):
    class Role(models.TextChoices):
        CLIENT = "client", "Client"
        EDITOR = "editor", "Editor"
        SUPPORT = "support", "Support"
        SUPERVISOR = "supervisor", "Supervisor"
        ADMIN = "admin", "Admin"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CLIENT,
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
    )

    avatar = models.ImageField(
        upload_to="users/avatars/",
        blank=True,
        null=True,
    )

    is_verified = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.username} ({self.role})"
    
class EditorProfile(models.Model):
    class EditorLevel(models.TextChoices):
        JUNIOR = "junior", "Junior"
        MID = "mid", "Mid"
        SENIOR = "senior", "Senior"
        PRO = "pro", "Pro"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="editor_profile",
    )
    display_name = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True)

    level = models.CharField(
        max_length=20,
        choices=EditorLevel.choices,
        default=EditorLevel.JUNIOR,
    )

    skills = models.ManyToManyField(
        EditStyle,
        related_name="editor_profiles",
        blank=True,
    )

    base_price = models.PositiveIntegerField(default=0)
    average_delivery_hours = models.PositiveIntegerField(default=24)

    rating_average = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
    )
    completed_orders_count = models.PositiveIntegerField(default=0)

    is_available = models.BooleanField(default=True)
    accepts_direct_requests = models.BooleanField(default=True)
    accepts_public_requests = models.BooleanField(default=True)
    accepts_sample_challenges = models.BooleanField(default=True)

    admin_note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-rating_average", "-completed_orders_count", "user__username"]
        verbose_name = "Editor profile"
        verbose_name_plural = "Editor profiles"

    def __str__(self):
        return self.display_name or self.user.get_username()


class EditorPortfolioItem(models.Model):
    editor = models.ForeignKey(
        EditorProfile,
        on_delete=models.CASCADE,
        related_name="portfolio_items",
    )
    style = models.ForeignKey(
        EditStyle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="portfolio_items",
    )

    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    before_image = models.ImageField(
        upload_to="editor_portfolio/before/",
        blank=True,
        null=True,
    )
    after_image = models.ImageField(
        upload_to="editor_portfolio/after/",
        blank=True,
        null=True,
    )

    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["editor", "sort_order", "-created_at"]
        verbose_name = "Editor portfolio item"
        verbose_name_plural = "Editor portfolio items"

    def __str__(self):
        return f"{self.editor} - {self.title}"