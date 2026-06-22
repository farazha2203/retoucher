from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "role",
        "phone_number",
        "is_verified",
        "is_staff",
        "is_active",
        "date_joined",
    )
    list_filter = (
        "role",
        "is_verified",
        "is_staff",
        "is_active",
    )
    search_fields = (
        "username",
        "email",
        "phone_number",
    )
    ordering = ("-date_joined",)

    fieldsets = UserAdmin.fieldsets + (
        (
            "Retoucher Profile",
            {
                "fields": (
                    "role",
                    "phone_number",
                    "avatar",
                    "is_verified",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Retoucher Profile",
            {
                "fields": (
                    "role",
                    "phone_number",
                    "is_verified",
                )
            },
        ),
    )