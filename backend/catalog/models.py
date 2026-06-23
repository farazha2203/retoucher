from django.db import models


class EditCategory(models.Model):
    title = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "title"]
        verbose_name = "Edit category"
        verbose_name_plural = "Edit categories"

    def __str__(self):
        return self.title


class EditStyle(models.Model):
    category = models.ForeignKey(
        EditCategory,
        on_delete=models.CASCADE,
        related_name="styles",
    )
    title = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)

    min_price = models.PositiveIntegerField(default=0)
    max_price = models.PositiveIntegerField(default=0)
    suggested_price = models.PositiveIntegerField(default=0)

    estimated_delivery_hours = models.PositiveIntegerField(default=24)

    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category__sort_order", "sort_order", "title"]
        unique_together = ["category", "title"]
        verbose_name = "Edit style"
        verbose_name_plural = "Edit styles"

    def __str__(self):
        return f"{self.category.title} - {self.title}"


class EditPackage(models.Model):
    class PackageLevel(models.TextChoices):
        BASIC = "basic", "Basic"
        STANDARD = "standard", "Standard"
        PREMIUM = "premium", "Premium"

    style = models.ForeignKey(
        EditStyle,
        on_delete=models.CASCADE,
        related_name="packages",
    )
    title = models.CharField(max_length=120)
    level = models.CharField(
        max_length=20,
        choices=PackageLevel.choices,
        default=PackageLevel.STANDARD,
    )
    description = models.TextField(blank=True)

    price = models.PositiveIntegerField(default=0)
    min_images = models.PositiveIntegerField(default=1)
    max_images = models.PositiveIntegerField(default=1)

    estimated_delivery_hours = models.PositiveIntegerField(default=24)
    includes_revision = models.BooleanField(default=True)
    revision_count = models.PositiveIntegerField(default=1)

    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["style__sort_order", "sort_order", "price"]
        unique_together = ["style", "level", "title"]
        verbose_name = "Edit package"
        verbose_name_plural = "Edit packages"

    def __str__(self):
        return f"{self.style.title} - {self.title}"