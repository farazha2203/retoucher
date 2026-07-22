from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html

from . import services as payment_services
from .models import (
    PaymentRequest,
    SiteCommissionSetting,
    Transaction,
    Wallet,
    WithdrawRequest,
)


def money(value):
    if value is None:
        return "—"
    return f"{int(value):,} تومان"


def admin_change_url(app_label, model_name, object_id):
    return reverse(f"admin:{app_label}_{model_name}_change", args=[object_id])


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = (
        "user_link",
        "role_badge",
        "balance_display",
        "frozen_display",
        "withdrawable_display",
        "available_display",
        "updated_at",
    )
    search_fields = (
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
    )
    list_filter = ("user__role",)
    list_select_related = ("user",)
    readonly_fields = (
        "user",
        "balance",
        "frozen_balance",
        "withdrawable_balance",
        "available_balance_field",
        "created_at",
        "updated_at",
    )
    ordering = ("-balance",)
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def user_link(self, obj):
        url = admin_change_url("accounts", "user", obj.user_id)
        return format_html('<a href="{}">{}</a>', url, obj.user.username)

    user_link.short_description = "کاربر"
    user_link.admin_order_field = "user__username"

    def role_badge(self, obj):
        role = getattr(obj.user, "role", "")
        colors = {
            "client": "#3b82f6",
            "editor": "#10b981",
            "admin": "#ef4444",
            "support": "#f59e0b",
        }
        color = colors.get(role, "#6b7280")
        label = obj.user.get_role_display() if hasattr(obj.user, "get_role_display") else role
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:11px">{}</span>',
            color,
            label or "—",
        )

    role_badge.short_description = "نقش"

    def balance_display(self, obj):
        return format_html("<b>{}</b>", money(obj.balance))

    balance_display.short_description = "موجودی"
    balance_display.admin_order_field = "balance"

    def frozen_display(self, obj):
        if obj.frozen_balance > 0:
            return format_html('<span style="color:#f59e0b">{}</span>', money(obj.frozen_balance))
        return "—"

    frozen_display.short_description = "بلوکه"
    frozen_display.admin_order_field = "frozen_balance"

    def withdrawable_display(self, obj):
        if obj.withdrawable_balance > 0:
            return format_html('<span style="color:#10b981">{}</span>', money(obj.withdrawable_balance))
        return "—"

    withdrawable_display.short_description = "قابل برداشت"
    withdrawable_display.admin_order_field = "withdrawable_balance"

    def available_display(self, obj):
        return money(obj.available_balance)

    available_display.short_description = "در دسترس"

    def available_balance_field(self, obj):
        return money(obj.available_balance)

    available_balance_field.short_description = "موجودی در دسترس"


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_link",
        "tx_type_badge",
        "status_badge",
        "amount_display",
        "balance_before_display",
        "balance_after_display",
        "order_link",
        "created_at",
    )
    list_filter = ("tx_type", "status", "created_at")
    search_fields = (
        "wallet__user__username",
        "wallet__user__email",
        "description",
        "order__id",
        "payment_request__ref_id",
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
    list_select_related = (
        "wallet",
        "wallet__user",
        "order",
        "payment_request",
        "created_by",
    )
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def user_link(self, obj):
        url = admin_change_url("accounts", "user", obj.wallet.user_id)
        return format_html('<a href="{}">{}</a>', url, obj.wallet.user.username)

    user_link.short_description = "کاربر"
    user_link.admin_order_field = "wallet__user__username"

    def tx_type_badge(self, obj):
        colors = {
            Transaction.TxType.DEPOSIT: "#3b82f6",
            Transaction.TxType.ESCROW_HOLD: "#f59e0b",
            Transaction.TxType.ESCROW_RELEASE: "#6b7280",
            Transaction.TxType.PAYMENT: "#ef4444",
            Transaction.TxType.COMMISSION: "#8b5cf6",
            Transaction.TxType.EDITOR_EARNING: "#10b981",
            Transaction.TxType.WITHDRAWAL: "#f97316",
            Transaction.TxType.REFUND: "#06b6d4",
            Transaction.TxType.ADMIN_ADJUSTMENT: "#64748b",
        }
        color = colors.get(obj.tx_type, "#6b7280")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:11px">{}</span>',
            color,
            obj.get_tx_type_display(),
        )

    tx_type_badge.short_description = "نوع"
    tx_type_badge.admin_order_field = "tx_type"

    def status_badge(self, obj):
        colors = {
            Transaction.Status.SUCCESS: "#10b981",
            Transaction.Status.PENDING: "#f59e0b",
            Transaction.Status.FAILED: "#ef4444",
            Transaction.Status.REVERSED: "#6b7280",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html('<b style="color:{}">{}</b>', color, obj.get_status_display())

    status_badge.short_description = "وضعیت"
    status_badge.admin_order_field = "status"

    def amount_display(self, obj):
        return money(obj.amount)

    amount_display.short_description = "مبلغ"
    amount_display.admin_order_field = "amount"

    def balance_before_display(self, obj):
        return money(obj.balance_before)

    balance_before_display.short_description = "قبل"

    def balance_after_display(self, obj):
        return money(obj.balance_after)

    balance_after_display.short_description = "بعد"
    balance_after_display.admin_order_field = "balance_after"

    def order_link(self, obj):
        if obj.order_id:
            url = admin_change_url("orders", "order", obj.order_id)
            return format_html('<a href="{}">#{}</a>', url, obj.order_id)
        return "—"

    order_link.short_description = "سفارش"


@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_link",
        "gateway_badge",
        "status_badge",
        "amount_display",
        "ref_id",
        "order_link",
        "created_at",
        "paid_at",
    )
    list_filter = ("gateway", "status", "created_at", "paid_at")
    search_fields = (
        "user__username",
        "user__email",
        "authority",
        "ref_id",
        "description",
        "order__id",
    )
    readonly_fields = (
        "authority",
        "ref_id",
        "gateway_response",
        "created_at",
        "paid_at",
    )
    list_select_related = ("user", "order")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_per_page = 50

    def has_delete_permission(self, request, obj=None):
        if obj and obj.ref_id:
            return False
        return super().has_delete_permission(request, obj=obj)

    def user_link(self, obj):
        url = admin_change_url("accounts", "user", obj.user_id)
        return format_html('<a href="{}">{}</a>', url, obj.user.username)

    user_link.short_description = "کاربر"
    user_link.admin_order_field = "user__username"

    def gateway_badge(self, obj):
        return format_html("<small>{}</small>", obj.get_gateway_display())

    gateway_badge.short_description = "درگاه"
    gateway_badge.admin_order_field = "gateway"

    def status_badge(self, obj):
        colors = {
            PaymentRequest.Status.CREATED: "#6b7280",
            PaymentRequest.Status.REDIRECTED: "#f59e0b",
            PaymentRequest.Status.SUCCESS: "#10b981",
            PaymentRequest.Status.FAILED: "#ef4444",
            PaymentRequest.Status.CANCELLED: "#94a3b8",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html('<b style="color:{}">{}</b>', color, obj.get_status_display())

    status_badge.short_description = "وضعیت"
    status_badge.admin_order_field = "status"

    def amount_display(self, obj):
        return money(obj.amount)

    amount_display.short_description = "مبلغ"
    amount_display.admin_order_field = "amount"

    def order_link(self, obj):
        if obj.order_id:
            url = admin_change_url("orders", "order", obj.order_id)
            return format_html('<a href="{}">#{}</a>', url, obj.order_id)
        return "—"

    order_link.short_description = "سفارش"


@admin.register(WithdrawRequest)
class WithdrawRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "editor_link",
        "amount_display",
        "status_badge",
        "bank_info_display",
        "created_at",
        "reviewed_by",
        "reviewed_at",
        "paid_at",
    )
    list_filter = ("status", "created_at", "reviewed_at", "paid_at")
    search_fields = (
        "editor__username",
        "editor__email",
        "card_number",
        "iban",
        "account_holder_name",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "reviewed_by",
        "reviewed_at",
        "paid_at",
    )
    list_select_related = ("editor", "reviewed_by")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_per_page = 50
    actions = (
        "action_approve",
        "action_reject",
        "action_mark_paid",
    )

    def editor_link(self, obj):
        url = admin_change_url("accounts", "user", obj.editor_id)
        return format_html('<a href="{}">{}</a>', url, obj.editor.username)

    editor_link.short_description = "ادیتور"
    editor_link.admin_order_field = "editor__username"

    def amount_display(self, obj):
        return format_html("<b>{}</b>", money(obj.amount))

    amount_display.short_description = "مبلغ"
    amount_display.admin_order_field = "amount"

    def status_badge(self, obj):
        colors = {
            WithdrawRequest.Status.PENDING: "#f59e0b",
            WithdrawRequest.Status.APPROVED: "#3b82f6",
            WithdrawRequest.Status.REJECTED: "#ef4444",
            WithdrawRequest.Status.PAID: "#10b981",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:11px">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "وضعیت"
    status_badge.admin_order_field = "status"

    def bank_info_display(self, obj):
        return format_html(
            "<small>{} | {} | {}</small>",
            obj.bank_name or "—",
            obj.card_number or "—",
            obj.account_holder_name or "—",
        )

    bank_info_display.short_description = "بانک / کارت"

    @admin.action(description="✅ تأیید درخواست‌های انتخابی")
    def action_approve(self, request, queryset):
        approved = 0
        skipped = queryset.exclude(status=WithdrawRequest.Status.PENDING).count()

        for wr in queryset.filter(status=WithdrawRequest.Status.PENDING):
            try:
                payment_services.approve_withdrawal(wr, admin_user=request.user)
                approved += 1
            except Exception as e:
                self.message_user(request, f"خطا برای #{wr.id}: {e}", messages.ERROR)

        if approved:
            self.message_user(request, f"{approved} درخواست تأیید شد.", messages.SUCCESS)
        if skipped:
            self.message_user(request, f"{skipped} درخواست به دلیل وضعیت نامعتبر رد شد.", messages.WARNING)

    @admin.action(description="❌ رد درخواست‌های انتخابی")
    def action_reject(self, request, queryset):
        rejected = 0
        skipped = queryset.exclude(status=WithdrawRequest.Status.PENDING).count()

        for wr in queryset.filter(status=WithdrawRequest.Status.PENDING):
            try:
                payment_services.reject_withdrawal(
                    wr,
                    admin_user=request.user,
                    note="رد دسته‌ای توسط ادمین",
                )
                rejected += 1
            except Exception as e:
                self.message_user(request, f"خطا برای #{wr.id}: {e}", messages.ERROR)

        if rejected:
            self.message_user(request, f"{rejected} درخواست رد شد.", messages.SUCCESS)
        if skipped:
            self.message_user(request, f"{skipped} درخواست به دلیل وضعیت نامعتبر رد شد.", messages.WARNING)

    @admin.action(description="💳 علامت‌گذاری به عنوان پرداخت‌شده")
    def action_mark_paid(self, request, queryset):
        paid = 0
        skipped = queryset.exclude(status=WithdrawRequest.Status.APPROVED).count()

        for wr in queryset.filter(status=WithdrawRequest.Status.APPROVED):
            try:
                payment_services.mark_withdrawal_paid(wr, admin_user=request.user)
                paid += 1
            except Exception as e:
                self.message_user(request, f"خطا برای #{wr.id}: {e}", messages.ERROR)

        if paid:
            self.message_user(request, f"{paid} درخواست پرداخت‌شده علامت‌گذاری شد.", messages.SUCCESS)
        if skipped:
            self.message_user(request, f"{skipped} درخواست به دلیل وضعیت نامعتبر رد شد.", messages.WARNING)


@admin.register(SiteCommissionSetting)
class SiteCommissionSettingAdmin(admin.ModelAdmin):
    list_display = (
        "commission_percent",
        "min_commission_display",
        "is_active_badge",
        "created_by",
        "created_at",
    )
    list_filter = ("is_active", "created_at")
    search_fields = ("note", "created_by__username", "created_by__email")
    readonly_fields = ("created_at", "created_by")
    ordering = ("-created_at",)
    list_per_page = 50

    def min_commission_display(self, obj):
        return money(obj.min_commission)

    min_commission_display.short_description = "حداقل کمیسیون"
    min_commission_display.admin_order_field = "min_commission"

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<b style="color:#10b981">✓ فعال</b>')
        return format_html('<span style="color:#6b7280">غیرفعال</span>')

    is_active_badge.short_description = "وضعیت"
    is_active_badge.admin_order_field = "is_active"

    def save_model(self, request, obj, form, change):
        if obj.is_active:
            SiteCommissionSetting.objects.exclude(pk=obj.pk).update(is_active=False)
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)