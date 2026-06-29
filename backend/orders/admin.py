from django.contrib import admin

from .models import (
    Order,
    OrderActivityLog,
    OrderComment,
    OrderDelivery,
    OrderImage,
    OrderNotification,
    OrderRating,
    OrderRevision,
    OrderStatusHistory,
)


class OrderImageInline(admin.TabularInline):
    model = OrderImage
    extra = 0
    readonly_fields = ("uploaded_at",)


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
    date_hierarchy = "created_at"
    inlines = (OrderImageInline,)
    list_select_related = (
        "client",
        "editor",
    )
    raw_id_fields = (
        "client",
        "editor",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "revision_count",
    )

    fieldsets = (
        ("Main", {
            "fields": (
                "title",
                "description",
                "status",
            )
        }),
        ("People", {
            "fields": (
                "client",
                "editor",
            )
        }),
        ("Timing", {
            "fields": (
                "deadline",
                "created_at",
                "updated_at",
            )
        }),
        ("Counters", {
            "fields": (
                "revision_count",
            )
        }),
    )


@admin.register(OrderDelivery)
class OrderDeliveryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "uploaded_by",
        "publication_status",
        "uploaded_at",
    )
    search_fields = (
        "order__title",
        "uploaded_by__username",
        "uploaded_by__email",
        "note",
    )
    list_filter = (
        "publication_status",
        "uploaded_at",
    )
    ordering = ("-uploaded_at",)
    date_hierarchy = "uploaded_at"
    list_select_related = (
        "order",
        "uploaded_by",
    )
    raw_id_fields = (
        "order",
        "uploaded_by",
    )
    readonly_fields = ("uploaded_at",)

    fieldsets = (
        ("Main", {
            "fields": (
                "order",
                "uploaded_by",
                "file",
                "note",
            )
        }),
        ("Publication", {
            "fields": (
                "publication_status",
            )
        }),
        ("Metadata", {
            "fields": (
                "uploaded_at",
            )
        }),
    )


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
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_select_related = (
        "order",
        "requested_by",
    )
    raw_id_fields = (
        "order",
        "requested_by",
    )
    readonly_fields = (
        "created_at",
    )

    fieldsets = (
        ("Main", {
            "fields": (
                "order",
                "source",
                "requested_by",
                "note",
            )
        }),
        ("Metadata", {
            "fields": (
                "created_at",
            )
        }),
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
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_select_related = (
        "order",
        "rated_by",
    )
    raw_id_fields = (
        "order",
        "rated_by",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Main", {
            "fields": (
                "order",
                "source",
                "rated_by",
                "score",
                "comment",
            )
        }),
        ("Metadata", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
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
    ordering = ("-uploaded_at",)
    date_hierarchy = "uploaded_at"
    list_select_related = ("order",)
    raw_id_fields = ("order",)
    readonly_fields = ("uploaded_at",)


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
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_select_related = (
        "order",
        "sender",
        "resolved_by",
    )
    raw_id_fields = (
        "order",
        "sender",
        "parent",
        "image",
        "delivery",
        "revision",
        "resolved_by",
    )
    readonly_fields = (
        "is_edited",
        "edited_at",
        "deleted_at",
        "created_at",
        "updated_at",
        "resolved_at",
    )

    fieldsets = (
        ("Main", {
            "fields": (
                "order",
                "sender",
                "text",
                "target_type",
                "status",
            )
        }),
        ("Relations", {
            "fields": (
                "parent",
                "image",
                "delivery",
                "revision",
            )
        }),
        ("Moderation", {
            "fields": (
                "resolved_by",
                "resolved_at",
                "deleted_at",
            )
        }),
        ("Edit State", {
            "fields": (
                "is_edited",
                "edited_at",
            )
        }),
        ("Metadata", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
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
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_select_related = (
        "order",
        "changed_by",
    )
    raw_id_fields = (
        "order",
        "changed_by",
    )
    readonly_fields = (
        "created_at",
    )

    fieldsets = (
        ("Main", {
            "fields": (
                "order",
                "from_status",
                "to_status",
                "changed_by",
                "note",
            )
        }),
        ("Metadata", {
            "fields": (
                "created_at",
            )
        }),
    )


@admin.register(OrderActivityLog)
class OrderActivityLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "activity_type",
        "actor",
        "created_at",
    )
    search_fields = (
        "order__title",
        "actor__username",
        "actor__email",
        "message",
    )
    list_filter = (
        "activity_type",
        "created_at",
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_select_related = (
        "order",
        "actor",
    )
    raw_id_fields = (
        "order",
        "actor",
    )
    readonly_fields = (
        "created_at",
    )

    fieldsets = (
        ("Main", {
            "fields": (
                "order",
                "activity_type",
                "actor",
                "message",
            )
        }),
        ("Metadata", {
            "fields": (
                "created_at",
            )
        }),
    )


@admin.register(OrderNotification)
class OrderNotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "recipient",
        "actor",
        "notification_type",
        "is_read",
        "created_at",
        "read_at",
    )
    search_fields = (
        "order__title",
        "recipient__username",
        "recipient__email",
        "actor__username",
        "actor__email",
        "title",
        "message",
    )
    list_filter = (
        "notification_type",
        "created_at",
        "read_at",
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_select_related = (
        "order",
        "recipient",
        "actor",
        "activity_log",
    )
    raw_id_fields = (
        "order",
        "recipient",
        "actor",
        "activity_log",
    )
    readonly_fields = (
        "created_at",
    )

    fieldsets = (
        ("Main", {
            "fields": (
                "order",
                "recipient",
                "actor",
                "notification_type",
                "title",
                "message",
            )
        }),
        ("State", {
            "fields": (
                "is_read",
                "read_at",
            )
        }),
        ("Relations", {
            "fields": (
                "activity_log",
            )
        }),
        ("Metadata", {
            "fields": (
                "created_at",
            )
        }),
    )