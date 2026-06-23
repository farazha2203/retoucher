from django.contrib import admin

from .models import (
    Order,
    OrderComment,
    OrderDelivery,
    OrderImage,
    OrderRating,
    OrderRevision,
    OrderStatusHistory,
)


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
        "updated_at",
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
        "updated_at",
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

@admin.register(OrderComment)
class OrderCommentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "sender",
        "target_type",
        "status",
        "is_edited",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "order__title",
        "sender__username",
        "sender__email",
        "text",
    )
    list_filter = (
        "target_type",
        "status",
        "is_edited",
        "created_at",
    )

@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "from_status",
        "to_status",
        "changed_by",
        "created_at",
    )
    search_fields = (
        "order__title",
        "changed_by__username",
        "changed_by__email",
        "note",
    )
    list_filter = (
        "from_status",
        "to_status",
        "created_at",
    )
