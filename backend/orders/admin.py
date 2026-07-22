from django.contrib import admin
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

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


def money(value):
    if value is None:
        return "—"
    return f"{int(value):,} تومان"


def admin_change_url(app_label, model_name, object_id):
    return reverse(f"admin:{app_label}_{model_name}_change", args=[object_id])


class OrderImageInline(admin.TabularInline):
    model = OrderImage
    extra = 0
    readonly_fields = ("uploaded_at",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "client_link",
        "editor_link",
        "status_badge",
        "agreed_price_display",
        "escrow_badge",
        "settlement_badge",
        "commission_display",
        "editor_earning_display",
        "revision_count",
        "deadline",
        "created_at",
    )
    list_filter = (
        "status",
        "escrow_held",
        "payment_settled",
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
        "commission_amount",
        "editor_earning",
        "payment_settled",
        "settlement_admin_link",
    )
    list_per_page = 50
    actions = (
        "mark_settlement_pending",
        "clear_settlement_flags",
    )

    fieldsets = (
        (
            "Main",
            {
                "fields": (
                    "title",
                    "description",
                    "status",
                )
            },
        ),
        (
            "People",
            {
                "fields": (
                    "client",
                    "editor",
                )
            },
        ),
        (
            "Financial / Settlement",
            {
                "fields": (
                    "agreed_price",
                    "escrow_held",
                    "payment_settled",
                    "commission_amount",
                    "editor_earning",
                    "settlement_admin_link",
                )
            },
        ),
        (
            "Timing",
            {
                "fields": (
                    "deadline",
                    "created_at",
                    "updated_at",
                )
            },
        ),
        ("Counters", {"fields": ("revision_count",)}),
    )

    def client_link(self, obj):
        if not obj.client_id:
            return "—"
        url = admin_change_url("accounts", "user", obj.client_id)
        return format_html('<a href="{}">{}</a>', url, obj.client.username)

    client_link.short_description = "Client"
    client_link.admin_order_field = "client__username"

    def editor_link(self, obj):
        if not obj.editor_id:
            return "—"
        url = admin_change_url("accounts", "user", obj.editor_id)
        return format_html('<a href="{}">{}</a>', url, obj.editor.username)

    editor_link.short_description = "Editor"
    editor_link.admin_order_field = "editor__username"

    def status_badge(self, obj):
        colors = {
            "draft": "#6b7280",
            "pending": "#f59e0b",
            "assigned": "#3b82f6",
            "in_progress": "#6366f1",
            "delivered": "#06b6d4",
            "revision_requested": "#f97316",
            "completed": "#10b981",
            "settlement_pending": "#8b5cf6",
            "paid": "#059669",
            "cancelled": "#ef4444",
        }
        color = colors.get(obj.status, "#6b7280")
        label = (
            obj.get_status_display()
            if hasattr(obj, "get_status_display")
            else obj.status
        )
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:11px">{}</span>',
            color,
            label,
        )

    status_badge.short_description = "Status"
    status_badge.admin_order_field = "status"

    def agreed_price_display(self, obj):
        if getattr(obj, "agreed_price", 0) > 0:
            return format_html("<b>{}</b>", money(obj.agreed_price))
        return "—"

    agreed_price_display.short_description = "Agreed price"
    agreed_price_display.admin_order_field = "agreed_price"

    def commission_display(self, obj):
        if getattr(obj, "commission_amount", 0) > 0:
            return format_html(
                '<span style="color:#8b5cf6">{}</span>',
                money(obj.commission_amount),
            )
        return "—"

    commission_display.short_description = "Commission"
    commission_display.admin_order_field = "commission_amount"

    def editor_earning_display(self, obj):
        if getattr(obj, "editor_earning", 0) > 0:
            return format_html(
                '<span style="color:#10b981">{}</span>',
                money(obj.editor_earning),
            )
        return "—"

    editor_earning_display.short_description = "Editor earning"
    editor_earning_display.admin_order_field = "editor_earning"

    def escrow_badge(self, obj):
        if getattr(obj, "escrow_held", False):
            return format_html(
                '<span style="background:#f59e0b;color:white;padding:2px 8px;border-radius:4px;font-size:11px">Escrow</span>'
            )
        return format_html('<span style="color:#6b7280">—</span>')

    escrow_badge.short_description = "Escrow"
    escrow_badge.admin_order_field = "escrow_held"

    def settlement_badge(self, obj):
        if getattr(obj, "payment_settled", False):
            return format_html(
                '<span style="background:#10b981;color:white;padding:2px 8px;border-radius:4px;font-size:11px">Settled</span>'
            )
        return format_html(
            '<span style="background:#6b7280;color:white;padding:2px 8px;border-radius:4px;font-size:11px">Open</span>'
        )

    settlement_badge.short_description = "Settlement"
    settlement_badge.admin_order_field = "payment_settled"

    def settlement_admin_link(self, obj):
        if not obj.pk:
            return "بعد از ذخیره سفارش فعال می‌شود."

        # API route, not Django admin route
        url = f"/api/payments/settlement/{obj.pk}/detail/"
        return format_html(
            '<a href="{}" target="_blank" style="font-weight:bold">مشاهده جزئیات settlement</a>',
            url,
        )

    settlement_admin_link.short_description = "Settlement API"

    @admin.action(description="Mark selected orders as settlement pending")
    def mark_settlement_pending(self, request, queryset):
        updated = queryset.update(
            status=Order.Status.SETTLEMENT_PENDING,
            payment_settled=False,
        )
        self.message_user(
            request,
            f"{updated} order(s) marked as settlement pending.",
        )

    @admin.action(description="Clear selected settlement flags")
    def clear_settlement_flags(self, request, queryset):
        updated = queryset.update(
            escrow_held=False,
            payment_settled=False,
            commission_amount=0,
            editor_earning=0,
        )
        self.message_user(
            request,
            f"{updated} order(s) settlement flags cleared.",
        )


@admin.register(OrderDelivery)
class OrderDeliveryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "uploaded_by",
        "publication_status",
        "publication_requested_by",
        "publication_requested_at",
        "publication_reviewed_by",
        "publication_reviewed_at",
        "uploaded_at",
    )

    search_fields = (
        "order__title",
        "uploaded_by__username",
        "uploaded_by__email",
        "publication_requested_by__username",
        "publication_requested_by__email",
        "publication_reviewed_by__username",
        "publication_reviewed_by__email",
        "note",
        "publication_note",
    )

    list_filter = (
        "publication_status",
        "uploaded_at",
        "publication_requested_at",
        "publication_reviewed_at",
    )

    ordering = ("-uploaded_at",)
    date_hierarchy = "uploaded_at"

    list_select_related = (
        "order",
        "uploaded_by",
        "publication_requested_by",
        "publication_reviewed_by",
    )

    raw_id_fields = (
        "order",
        "uploaded_by",
    )

    readonly_fields = (
        "uploaded_at",
        "publication_requested_by",
        "publication_requested_at",
        "publication_reviewed_by",
        "publication_reviewed_at",
    )

    actions = (
        "approve_public_deliveries",
        "reject_public_deliveries",
        "mark_public_deliveries_requested",
        "mark_public_deliveries_private",
    )

    fieldsets = (
        (
            "Main",
            {
                "fields": (
                    "order",
                    "uploaded_by",
                    "file",
                    "note",
                )
            },
        ),
        (
            "Publication",
            {
                "fields": (
                    "publication_status",
                    "publication_note",
                    "publication_requested_by",
                    "publication_requested_at",
                    "publication_reviewed_by",
                    "publication_reviewed_at",
                )
            },
        ),
        ("Metadata", {"fields": ("uploaded_at",)}),
    )

    @admin.action(description="Approve selected public deliveries")
    def approve_public_deliveries(self, request, queryset):
        updated = queryset.update(
            publication_status="approved",
            publication_reviewed_by=request.user,
            publication_reviewed_at=timezone.now(),
        )
        self.message_user(
            request,
            f"{updated} delivery item(s) approved for public portfolio.",
        )

    @admin.action(description="Reject selected public deliveries")
    def reject_public_deliveries(self, request, queryset):
        updated = queryset.update(
            publication_status="rejected",
            publication_reviewed_by=request.user,
            publication_reviewed_at=timezone.now(),
        )
        self.message_user(
            request,
            f"{updated} delivery item(s) rejected for public portfolio.",
        )

    @admin.action(description="Mark selected deliveries as requested")
    def mark_public_deliveries_requested(self, request, queryset):
        updated = queryset.update(
            publication_status="requested",
            publication_requested_by=request.user,
            publication_requested_at=timezone.now(),
            publication_reviewed_by=None,
            publication_reviewed_at=None,
        )
        self.message_user(
            request,
            f"{updated} delivery item(s) marked as requested.",
        )

    @admin.action(description="Mark selected deliveries as private")
    def mark_public_deliveries_private(self, request, queryset):
        updated = queryset.update(
            publication_status="private",
            publication_requested_by=None,
            publication_requested_at=None,
            publication_reviewed_by=None,
            publication_reviewed_at=None,
        )
        self.message_user(
            request,
            f"{updated} delivery item(s) marked as private.",
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
    readonly_fields = ("created_at",)

    fieldsets = (
        (
            "Main",
            {
                "fields": (
                    "order",
                    "source",
                    "requested_by",
                    "note",
                )
            },
        ),
        ("Metadata", {"fields": ("created_at",)}),
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
        (
            "Main",
            {
                "fields": (
                    "order",
                    "source",
                    "rated_by",
                    "score",
                    "comment",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
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
        (
            "Main",
            {
                "fields": (
                    "order",
                    "sender",
                    "text",
                    "target_type",
                    "status",
                )
            },
        ),
        (
            "Relations",
            {
                "fields": (
                    "parent",
                    "image",
                    "delivery",
                    "revision",
                )
            },
        ),
        (
            "Moderation",
            {
                "fields": (
                    "resolved_by",
                    "resolved_at",
                    "deleted_at",
                )
            },
        ),
        (
            "Edit State",
            {
                "fields": (
                    "is_edited",
                    "edited_at",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
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
    readonly_fields = ("created_at",)

    fieldsets = (
        (
            "Main",
            {
                "fields": (
                    "order",
                    "from_status",
                    "to_status",
                    "changed_by",
                    "note",
                )
            },
        ),
        ("Metadata", {"fields": ("created_at",)}),
    )


@admin.register(OrderActivityLog)
class OrderActivityLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "activity_type",
        "actor",
        "tx_ref",
        "created_at",
    )
    search_fields = (
        "order__title",
        "actor__username",
        "actor__email",
        "message",
        "tx_ref",
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
    readonly_fields = ("created_at",)

    fieldsets = (
        (
            "Main",
            {
                "fields": (
                    "order",
                    "activity_type",
                    "actor",
                    "message",
                    "tx_ref",
                )
            },
        ),
        ("Metadata", {"fields": ("created_at",)}),
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
    readonly_fields = ("created_at",)

    fieldsets = (
        (
            "Main",
            {
                "fields": (
                    "order",
                    "recipient",
                    "actor",
                    "notification_type",
                    "title",
                    "message",
                )
            },
        ),
        (
            "State",
            {
                "fields": (
                    "is_read",
                    "read_at",
                )
            },
        ),
        ("Relations", {"fields": ("activity_log",)}),
        ("Metadata", {"fields": ("created_at",)}),
    )
