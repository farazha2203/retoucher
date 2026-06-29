from django.contrib import admin

from .models import (
    PaymentRequest,
    SiteCommissionSetting,
    Transaction,
    Wallet,
    WithdrawRequest,
)


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "balance",
        "frozen_balance",
        "withdrawable_balance",
        "updated_at",
    )
    search_fields = (
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
    )
    ordering = ("-id",)
    list_select_related = ("user",)
    raw_id_fields = ("user",)
    readonly_fields = (
        "balance",
        "frozen_balance",
        "withdrawable_balance",
        "updated_at",
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "wallet",
        "tx_type",
        "status",
        "amount",
        "balance_after",
        "order",
        "created_by",
        "created_at",
    )
    list_filter = (
        "tx_type",
        "status",
        "created_at",
    )
    search_fields = (
        "wallet__user__username",
        "wallet__user__email",
        "description",
    )
    ordering = ("-id",)
    date_hierarchy = "created_at"
    list_select_related = (
        "wallet",
        "wallet__user",
        "order",
        "payment_request",
        "created_by",
    )
    raw_id_fields = (
        "wallet",
        "order",
        "payment_request",
        "created_by",
    )
    readonly_fields = (
        "wallet",
        "tx_type",
        "status",
        "amount",
        "balance_before",
        "balance_after",
        "order",
        "payment_request",
        "description",
        "meta",
        "created_by",
        "created_at",
    )

    fieldsets = (
        ("Main", {
            "fields": (
                "wallet",
                "tx_type",
                "status",
                "amount",
            )
        }),
        ("Balance", {
            "fields": (
                "balance_before",
                "balance_after",
            )
        }),
        ("Relations", {
            "fields": (
                "order",
                "payment_request",
                "created_by",
            )
        }),
        ("Details", {
            "fields": (
                "description",
                "meta",
                "created_at",
            )
        }),
    )

    def has_add_permission(self, request):
        return False  # تراکنش‌ها فقط از طریق کد ایجاد می‌شوند

    def has_delete_permission(self, request, obj=None):
        return False  # برای حفظ یکپارچگی حسابداری بهتر است حذف مستقیم غیرفعال باشد


@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "gateway",
        "status",
        "amount",
        "authority",
        "ref_id",
        "created_at",
        "paid_at",
    )
    list_filter = (
        "gateway",
        "status",
        "created_at",
        "paid_at",
    )
    search_fields = (
        "user__username",
        "user__email",
        "authority",
        "ref_id",
    )
    ordering = ("-id",)
    date_hierarchy = "created_at"
    list_select_related = ("user",)
    raw_id_fields = ("user",)
    readonly_fields = (
        "authority",
        "ref_id",
        "gateway_response",
        "created_at",
        "paid_at",
    )

    fieldsets = (
        ("Main", {
            "fields": (
                "user",
                "gateway",
                "status",
                "amount",
            )
        }),
        ("Gateway", {
            "fields": (
                "authority",
                "ref_id",
                "gateway_response",
            )
        }),
        ("Timestamps", {
            "fields": (
                "created_at",
                "paid_at",
            )
        }),
    )


@admin.register(WithdrawRequest)
class WithdrawRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "editor",
        "amount",
        "status",
        "created_at",
        "updated_at",
        "paid_at",
    )
    list_filter = (
        "status",
        "created_at",
        "paid_at",
    )
    search_fields = (
        "editor__username",
        "editor__email",
        "card_number",
        "iban",
    )
    ordering = ("-id",)
    date_hierarchy = "created_at"
    list_select_related = ("editor",)
    raw_id_fields = ("editor",)
    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        ("Main", {
            "fields": (
                "editor",
                "amount",
                "status",
            )
        }),
        ("Payout Info", {
            "fields": (
                "card_number",
                "iban",
            )
        }),
        ("Timestamps", {
            "fields": (
                "created_at",
                "updated_at",
                "paid_at",
            )
        }),
    )


@admin.register(SiteCommissionSetting)
class SiteCommissionSettingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "commission_percent",
        "min_commission",
        "is_active",
        "created_at",
    )
    list_filter = (
        "is_active",
        "created_at",
    )
    ordering = ("-id",)
    readonly_fields = ("created_at",)

    fieldsets = (
        ("Commission", {
            "fields": (
                "commission_percent",
                "min_commission",
                "is_active",
            )
        }),
        ("Metadata", {
            "fields": (
                "created_at",
            )
        }),
    )