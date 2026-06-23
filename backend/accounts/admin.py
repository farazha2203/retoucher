from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, EditorPortfolioItem, EditorProfile


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "id",
        "username",
        "email",
        "role",
        "is_staff",
        "is_superuser",
        "is_active",
        "date_joined",
    )
    list_filter = (
        "role",
        "is_staff",
        "is_superuser",
        "is_active",
        "date_joined",
    )
    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
    )
    ordering = ("id",)

    fieldsets = UserAdmin.fieldsets + (
        (
            "Retoucher Role",
            {
                "fields": (
                    "role",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Retoucher Role",
            {
                "fields": (
                    "role",
                )
            },
        ),
    )



class EditorPortfolioItemInline(admin.TabularInline):
    model = EditorPortfolioItem
    extra = 0
    fields = (
        "title",
        "style",
        "before_image",
        "after_image",
        "is_featured",
        "is_active",
        "sort_order",
    )


@admin.register(EditorProfile)
class EditorProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "display_name",
        "level",
        "base_price",
        "average_delivery_hours",
        "rating_average",
        "completed_orders_count",
        "is_available",
        "accepts_direct_requests",
        "accepts_public_requests",
        "accepts_sample_challenges",
    )
    list_filter = (
        "level",
        "is_available",
        "accepts_direct_requests",
        "accepts_public_requests",
        "accepts_sample_challenges",
        "skills",
    )
    search_fields = (
        "user__username",
        "user__email",
        "display_name",
        "bio",
    )
    filter_horizontal = ("skills",)
    inlines = [EditorPortfolioItemInline]


@admin.register(EditorPortfolioItem)
class EditorPortfolioItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "editor",
        "title",
        "style",
        "is_featured",
        "is_active",
        "sort_order",
        "created_at",
    )
    list_filter = ("is_featured", "is_active", "style", "style__category")
    search_fields = (
        "title",
        "description",
        "editor__user__username",
        "editor__display_name",
    )
    ordering = ("editor", "sort_order", "-created_at")