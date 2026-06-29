from decimal import Decimal

from django.contrib import admin, messages
from django.db.models import Sum
from django.utils.html import format_html
from django.utils import timezone

from . import services as payment_services
from .models import PaymentRequest, SiteCommissionSetting, Transaction, Wallet, WithdrawRequest


# ─── Wallet ───────────────────────────────────────────────────────────────────

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = [
        "user", "role_badge", "balance_display",
        "frozen_display", "withdrawable_display",
        "available_display", "updated_at",
    ]
    search_fields = ["user__username", "user__email", "user__first_name", "user__last_name"]
    list_filter = ["user__role"]
    readonly_fields = [
        "balance", "frozen_balance", "withdrawable_balance",
        "available_balance_field", "updated_at", "created_at",
    ]

    def role_badge(self, obj):
        colors = {"client": "#3b82f6", "editor": "#10b981", "admin": "#ef4444", "support": "#f59e0b"}
        color = colors.get(obj.user.role, "#6b7280")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:11px">{}</span>',
            color, obj.user.get_role_display() if hasattr(obj.user, 'get_role_display') else obj.user.role,
        )
    role_badge.short_description = "نقش"

    def balance_display(self, obj):
        return format_html('<b>{:,}</b> تومان', int(obj.balance))
    balance_display.short_description = "موجودی"

    def frozen_display(self, obj):
        if obj.frozen_balance > 0:
            return format_html('<span style="color:#f59e0b">{:,}</span>', int(obj.frozen_balance))
        return "—"
    frozen_display.short_description = "بلوکه"

    def withdrawable_display(self, obj):
        if obj.withdrawable_balance > 0:
            return format_html('<span style="color:#10b981">{:,}</span>', int(obj.withdrawable_balance))
        return "—"
    withdrawable_display.short_description = "قابل برداشت"

    def available_display(self, obj):
        return format_html('{:,}', int(obj.available_balance))
    available_display.short_description = "در دسترس"

    def available_balance_field(self, obj):
        return f"{obj.available_balance:,} تومان"
    available_balance_field.short_description = "موجودی در دسترس"


# ─── Transaction ──────────────────────────────────────────────────────────────

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        "id", "user_link", "tx_type_badge", "status_badge",
        "amount_display", "balance_after_display", "order_link", "created_at",
    ]
    list_filter = ["tx_type", "status", "created_at"]
    search_fields = [
        "wallet__user__username", "wallet__user__email",
        "description", "order__id",
    ]
    readonly_fields = [
        "wallet", "tx_type", "status", "amount",
        "balance_before", "balance_after", "order",
        "payment_request", "description", "meta", "created_by", "created_at",
    ]
    date_hierarchy = "created_at"
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def user_link(self, obj):
        return format_html('<a href="/admin/accounts/user/{}/change/">{}</a>', obj.wallet.user_id, obj.wallet.user.username)
    user_link.short_description = "کاربر"

    def tx_type_badge(self, obj):
        colors = {
            "deposit": "#3b82f6",
            "escrow_hold": "#f59e0b",
            "escrow_release": "#6b7280",
            "payment": "#ef4444",
            "commission": "#8b5cf6",
            "editor_earning": "#10b981",
            "withdrawal": "#f97316",
            "refund": "#06b6d4",
            "admin_adjustment": "#64748b",
        }
        color = colors.get(obj.tx_type, "#6b7280")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:11px">{}</span>',
            color, obj.get_tx_type_display(),
        )
    tx_type_badge.short_description = "نوع"

    def status_badge(self, obj):
        colors = {"success": "#10b981", "pending": "#f59e0b", "failed": "#ef4444", "reversed": "#6b7280"}
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="color:{}">{}</span>', color, obj.get_status_display()
        )
    status_badge.short_description = "وضعیت"

    def amount_display(self, obj):
        return format_html('{:,} ت', int(obj.amount))
    amount_display.short_description = "مبلغ"

    def balance_after_display(self, obj):
        return format_html('{:,} ت', int(obj.balance_after))
    balance_after_display.short_description = "موجودی پس از"

    def order_link(self, obj):
        if obj.order_id:
            return format_html('<a href="/admin/orders/order/{}/change/">#{}</a>', obj.order_id, obj.order_id)
        return "—"
    order_link.short_description = "سفارش"


# ─── PaymentRequest ───────────────────────────────────────────────────────────

@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):
    list_display = [
        "id", "user_link", "gateway_badge", "status_badge",
        "amount_display", "ref_id", "order_link", "created_at", "paid_at",
    ]
    list_filter = ["gateway", "status", "created_at"]
    search_fields = ["user__username", "user__email", "authority", "ref_id"]
    readonly_fields = ["authority", "ref_id", "gateway_response", "created_at", "paid_at"]
    date_hierarchy = "created_at"

    def user_link(self, obj):
        return format_html('<a href="/admin/accounts/user/{}/change/">{}</a>', obj.user_id, obj.user.username)
    user_link.short_description = "کاربر"

    def gateway_badge(self, obj):
        return format_html('<span style="font-size:11px">{}</span>', obj.get_gateway_display())
    gateway_badge.short_description = "درگاه"

    def status_badge(self, obj):
        colors = {
            "created": "#6b7280", "redirected": "#f59e0b",
            "success": "#10b981", "failed": "#ef4444", "cancelled": "#94a3b8",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html('<span style="color:{};font-weight:bold">{}</span>', color, obj.get_status_display())
    status_badge.short_description = "وضعیت"

    def amount_display(self, obj):
        return format_html('{:,} ت', int(obj.amount))
    amount_display.short_description = "مبلغ"

    def order_link(self, obj):
        if obj.order_id:
            return format_html('<a href="/admin/orders/order/{}/change/">#{}</a>', obj.order_id, obj.order_id)
        return "—"
    order_link.short_description = "سفارش"


# ─── WithdrawRequest ──────────────────────────────────────────────────────────

@admin.register(WithdrawRequest)
class WithdrawRequestAdmin(admin.ModelAdmin):
    list_display = [
        "id", "editor_link", "amount_display", "status_badge",
        "bank_info_display", "created_at", "reviewed_by", "paid_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["editor__username", "editor__email", "card_number", "iban"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"
    actions = ["action_approve", "action_reject", "action_mark_paid"]

    def editor_link(self, obj):
        return format_html('<a href="/admin/accounts/user/{}/change/">{}</a>', obj.editor_id, obj.editor.username)
    editor_link.short_description = "ادیتور"

    def amount_display(self, obj):
        return format_html('<b>{:,}</b> ت', int(obj.amount))
    amount_display.short_description = "مبلغ"

    def status_badge(self, obj):
        colors = {
            "pending": "#f59e0b", "approved": "#3b82f6",
            "rejected": "#ef4444", "paid": "#10b981",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:11px">{}</span>',
            color, obj.get_status_display(),
        )
    status_badge.short_description = "وضعیت"

    def bank_info_display(self, obj):
        return format_html('<small>{} | {}</small>', obj.bank_name or "—", obj.card_number or "—")
    bank_info_display.short_description = "بانک / کارت"

    @admin.action(description="✅ تأیید درخواست‌های انتخابی")
    def action_approve(self, request, queryset):
        approved = 0
        for wr in queryset.filter(status=WithdrawRequest.Status.PENDING):
            try:
                payment_services.approve_withdrawal(wr, admin_user=request.user)
                approved += 1
            except Exception as e:
                self.message_user(request, f"خطا برای #{wr.id}: {e}", messages.ERROR)
        if approved:
            self.message_user(request, f"{approved} درخواست تأیید شد.", messages.SUCCESS)

    @admin.action(description="❌ رد درخواست‌های انتخابی")
    def action_reject(self, request, queryset):
        rejected = 0
        for wr in queryset.filter(status=WithdrawRequest.Status.PENDING):
            try:
                payment_services.reject_withdrawal(wr, admin_user=request.user, note="رد دسته‌ای توسط ادمین")
                rejected += 1
            except Exception as e:
                self.message_user(request, f"خطا برای #{wr.id}: {e}", messages.ERROR)
        if rejected:
            self.message_user(request, f"{rejected} درخواست رد شد.", messages.SUCCESS)

    @admin.action(description="💳 علامت‌گذاری به عنوان پرداخت‌شده")
    def action_mark_paid(self, request, queryset):
        paid = 0
        for wr in queryset.filter(status=WithdrawRequest.Status.APPROVED):
            try:
                payment_services.mark_withdrawal_paid(wr, admin_user=request.user)
                paid += 1
            except Exception as e:
                self.message_user(request, f"خطا برای #{wr.id}: {e}", messages.ERROR)
        if paid:
            self.message_user(request, f"{paid} درخواست پرداخت‌شده علامت‌گذاری شد.", messages.SUCCESS)


# ─── CommissionSetting ────────────────────────────────────────────────────────

@admin.register(SiteCommissionSetting)
class SiteCommissionSettingAdmin(admin.ModelAdmin):
    list_display = ["commission_percent", "min_commission", "is_active_badge", "created_by", "created_at"]
    list_filter = ["is_active"]
    readonly_fields = ["created_at", "created_by"]

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#10b981;font-weight:bold">✓ فعال</span>')
        return format_html('<span style="color:#6b7280">غیرفعال</span>')
    is_active_badge.short_description = "وضعیت"

    def save_model(self, request, obj, form, change):
        if obj.is_active:
            SiteCommissionSetting.objects.exclude(pk=obj.pk).update(is_active=False)
        obj.created_by = request.user
        super().save_model(request, obj, form, change)
