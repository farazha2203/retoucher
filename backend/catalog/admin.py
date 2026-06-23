from django.contrib import admin

from .models import EditCategory, EditPackage, EditStyle


@admin.register(EditCategory)
class EditCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "slug",
        "is_active",
        "sort_order",
        "created_at",
    )
    list_filter = ("is_active",)
    search_fields = ("title", "slug", "description")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("sort_order", "title")


@admin.register(EditStyle)
class EditStyleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "category",
        "min_price",
        "max_price",
        "suggested_price",
        "estimated_delivery_hours",
        "is_active",
        "sort_order",
    )
    list_filter = ("is_active", "category")
    search_fields = ("title", "slug", "description", "category__title")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("category__sort_order", "sort_order", "title")


@admin.register(EditPackage)
class EditPackageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "style",
        "level",
        "price",
        "min_images",
        "max_images",
        "estimated_delivery_hours",
        "includes_revision",
        "revision_count",
        "is_active",
    )
    list_filter = ("is_active", "level", "style__category", "style")
    search_fields = ("title", "description", "style__title", "style__category__title")
    ordering = ("style__category__sort_order", "style__sort_order", "sort_order", "price")