from django.contrib import admin

from .models import Order, OrderImage


class OrderImageInline(admin.TabularInline):
    model = OrderImage
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "client",
        "status",
        "deadline",
        "created_at",
    )
    list_filter = (
        "status",
        "created_at",
    )
    search_fields = (
        "title",
        "description",
        "client__username",
        "client__email",
    )
    ordering = ("-created_at",)
    inlines = (OrderImageInline,)


@admin.register(OrderImage)
class OrderImageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "image",
        "uploaded_at",
    )
    search_fields = (
        "order__title",
        "order__client__username",
    )