from django.contrib import admin

from .models import Order, OrderDelivery, OrderImage, OrderRating, OrderRevision


class OrderImageInline(admin.TabularInline):
    model = OrderImage
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "client",
        "editor",
        "status",
        "revision_count",
        "deadline",
        "created_at",
    )
    list_filter = (
        "status",
        "created_at",
        "deadline",
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
    list_filter = ("uploaded_at",)

@admin.register(OrderRevision)
class OrderRevisionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "source",
        "requested_by",
        "created_at",
    )
    search_fields = (
        "order__title",
        "requested_by__username",
        "requested_by__email",
        "note",
    )
    list_filter = (
        "source",
        "created_at",
    )

@admin.register(OrderRating)
class OrderRatingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "source",
        "rated_by",
        "score",
        "created_at",
    )
    search_fields = (
        "order__title",
        "rated_by__username",
        "rated_by__email",
        "comment",
    )
    list_filter = (
        "source",
        "score",
        "created_at",
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
