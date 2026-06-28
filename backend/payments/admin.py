from django.contrib import admin

from .models import PaymentRequest, SiteCommissionSetting, Transaction, Wallet, WithdrawRequest


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ["user", "balance", "frozen_balance", "withdrawable_balance", "updated_at"]
    search_fields = ["user__username", "user__email"]
    readonly_fields = ["balance", "frozen_balance", "withdrawable_balance", "updated_at"]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["id", "wallet", "tx_type", "status", "amount", "balance_after", "order", "created_at"]
    list_filter = ["tx_type", "status"]
    search_fields = ["wallet__user__username", "description"]
    readonly_fields = [
        "wallet", "tx_type", "status", "amount",
        "balance_before", "balance_after", "order",
        "payment_request", "description", "meta", "created_by", "created_at",
    ]

    def has_add_permission(self, request):
        return False  # تراکنش‌ها فقط از طریق کد ایجاد می‌شوند


@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "gateway", "status", "amount", "ref_id", "created_at"]
    list_filter = ["gateway", "status"]
    search_fields = ["user__username", "authority", "ref_id"]
    readonly_fields = ["authority", "ref_id", "gateway_response", "created_at", "paid_at"]


@admin.register(WithdrawRequest)
class WithdrawRequestAdmin(admin.ModelAdmin):
    list_display = ["id", "editor", "amount", "status", "created_at", "paid_at"]
    list_filter = ["status"]
    search_fields = ["editor__username", "card_number", "iban"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(SiteCommissionSetting)
class SiteCommissionSettingAdmin(admin.ModelAdmin):
    list_display = ["commission_percent", "min_commission", "is_active", "created_at"]
    list_filter = ["is_active"]
