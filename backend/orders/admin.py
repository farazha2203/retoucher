from django.contrib import admin

from .models import Order, OrderDelivery, OrderImage




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
        "editor",
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
        "editor__username",
        "editor__email",
    )
    ordering = ("-created_at",)
    inlines = (OrderImageInline,)

@admin.register(OrderDelivery)
class OrderDeliveryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "uploaded_by",
        "uploaded_at",
    )
    search_fields = (
        "order__title",
        "uploaded_by__username",
        "uploaded_by__email",
    )
    list_filter = (
        "uploaded_at",
    )

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