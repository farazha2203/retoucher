from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import PaymentRequest, SiteCommissionSetting, Transaction, Wallet, WithdrawRequest

User = get_user_model()


# ─── Wallet ───────────────────────────────────────────────────────────────────

class WalletSerializer(serializers.ModelSerializer):
    available_balance = serializers.SerializerMethodField()
    user_username = serializers.CharField(source="user.username", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)
    user_role = serializers.CharField(source="user.role", read_only=True)
    user_full_name = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = [
            "id", "user_username", "user_email", "user_role", "user_full_name",
            "balance", "frozen_balance", "withdrawable_balance",
            "available_balance", "updated_at",
        ]
        read_only_fields = fields

    def get_available_balance(self, obj):
        return obj.available_balance

    def get_user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username


# ─── Transaction ──────────────────────────────────────────────────────────────

class TransactionSerializer(serializers.ModelSerializer):
    tx_type_display = serializers.CharField(source="get_tx_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    order_id = serializers.IntegerField(source="order.id", read_only=True, allow_null=True)
    user_username = serializers.CharField(source="wallet.user.username", read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id", "user_username", "tx_type", "tx_type_display",
            "status", "status_display", "amount",
            "balance_before", "balance_after",
            "order_id", "description", "created_at",
        ]
        read_only_fields = fields


# ─── PaymentRequest ───────────────────────────────────────────────────────────

class PaymentRequestSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    gateway_display = serializers.CharField(source="get_gateway_display", read_only=True)
    user_username = serializers.CharField(source="user.username", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = PaymentRequest
        fields = [
            "id", "user_username", "user_email",
            "gateway", "gateway_display",
            "status", "status_display",
            "amount", "description",
            "ref_id", "authority",
            "order", "created_at", "paid_at",
        ]
        read_only_fields = fields


class PaymentRequestPublicSerializer(PaymentRequestSerializer):
    """نسخه عمومی — بدون authority"""
    class Meta(PaymentRequestSerializer.Meta):
        fields = [f for f in PaymentRequestSerializer.Meta.fields if f != "authority"]


# ─── WithdrawRequest ──────────────────────────────────────────────────────────

class WithdrawRequestSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    editor_username = serializers.CharField(source="editor.username", read_only=True)
    editor_email = serializers.CharField(source="editor.email", read_only=True)
    editor_full_name = serializers.SerializerMethodField()
    reviewed_by_username = serializers.CharField(source="reviewed_by.username", read_only=True, allow_null=True)

    class Meta:
        model = WithdrawRequest
        fields = [
            "id", "editor_username", "editor_email", "editor_full_name",
            "amount", "status", "status_display",
            "bank_name", "card_number", "iban", "account_holder_name",
            "editor_note", "admin_note",
            "reviewed_by_username", "reviewed_at",
            "created_at", "paid_at",
        ]
        read_only_fields = [
            "id", "editor_username", "editor_email", "editor_full_name",
            "status", "status_display", "admin_note",
            "reviewed_by_username", "reviewed_at", "created_at", "paid_at",
        ]

    def get_editor_full_name(self, obj):
        return f"{obj.editor.first_name} {obj.editor.last_name}".strip() or obj.editor.username


# ─── Input Serializers ────────────────────────────────────────────────────────

class InitiatePaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=14, decimal_places=0, min_value=Decimal("10000"))
    description = serializers.CharField(max_length=255, required=False, default="شارژ کیف‌پول")
    callback_url = serializers.URLField()
    order_id = serializers.IntegerField(required=False, allow_null=True)


class AdminDepositSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=0, min_value=Decimal("1000"))
    description = serializers.CharField(max_length=255, required=False, default="")


class CreateWithdrawSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=14, decimal_places=0, min_value=Decimal("50000"))
    bank_name = serializers.CharField(max_length=100)
    card_number = serializers.CharField(max_length=20)
    iban = serializers.CharField(max_length=30, required=False, default="")
    account_holder_name = serializers.CharField(max_length=150)
    editor_note = serializers.CharField(max_length=500, required=False, default="")

    def validate_card_number(self, value):
        digits = value.replace("-", "").replace(" ", "")
        if not digits.isdigit() or len(digits) != 16:
            raise serializers.ValidationError("شماره کارت باید ۱۶ رقم باشد.")
        return digits

    def validate_iban(self, value):
        if value and not value.startswith("IR"):
            raise serializers.ValidationError("شبا باید با IR شروع شود.")
        return value


class WithdrawReviewSerializer(serializers.Serializer):
    admin_note = serializers.CharField(max_length=500, required=False, default="")


# ─── Commission Setting ───────────────────────────────────────────────────────

class CommissionSettingSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source="created_by.username", read_only=True, allow_null=True)

    class Meta:
        model = SiteCommissionSetting
        fields = [
            "id", "commission_percent", "min_commission",
            "is_active", "note", "created_by_username", "created_at",
        ]
        read_only_fields = ["id", "created_by_username", "created_at"]


class CreateCommissionSettingSerializer(serializers.Serializer):
    commission_percent = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=Decimal("0"), max_value=Decimal("100"))
    min_commission = serializers.DecimalField(max_digits=10, decimal_places=0, min_value=Decimal("0"), required=False, default=Decimal("0"))
    note = serializers.CharField(max_length=500, required=False, default="")


# ─── گزارش‌ها / Dashboard ────────────────────────────────────────────────────

class PaymentSummarySerializer(serializers.Serializer):
    """خلاصه مالی برای ادمین"""
    total_deposits = serializers.DecimalField(max_digits=16, decimal_places=0)
    total_payments = serializers.DecimalField(max_digits=16, decimal_places=0)
    total_commissions = serializers.DecimalField(max_digits=16, decimal_places=0)
    total_editor_earnings = serializers.DecimalField(max_digits=16, decimal_places=0)
    total_withdrawals = serializers.DecimalField(max_digits=16, decimal_places=0)
    pending_withdrawals_count = serializers.IntegerField()
    pending_withdrawals_amount = serializers.DecimalField(max_digits=16, decimal_places=0)
    total_wallets = serializers.IntegerField()
    total_frozen = serializers.DecimalField(max_digits=16, decimal_places=0)
    failed_payments_count = serializers.IntegerField()
    period_label = serializers.CharField()


class InvoiceSerializer(serializers.Serializer):
    """صورت‌حساب برای کاربر"""
    invoice_number = serializers.CharField()
    user_username = serializers.CharField()
    user_email = serializers.CharField()
    user_full_name = serializers.CharField()
    generated_at = serializers.DateTimeField()
    period_from = serializers.DateTimeField(allow_null=True)
    period_to = serializers.DateTimeField(allow_null=True)
    transactions = TransactionSerializer(many=True)
    payment_requests = PaymentRequestPublicSerializer(many=True)
    total_deposited = serializers.DecimalField(max_digits=16, decimal_places=0)
    total_spent = serializers.DecimalField(max_digits=16, decimal_places=0)
    total_earned = serializers.DecimalField(max_digits=16, decimal_places=0)
    total_withdrawn = serializers.DecimalField(max_digits=16, decimal_places=0)
    current_balance = serializers.DecimalField(max_digits=16, decimal_places=0)
    withdrawable_balance = serializers.DecimalField(max_digits=16, decimal_places=0)
