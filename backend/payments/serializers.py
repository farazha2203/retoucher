from decimal import Decimal

from rest_framework import serializers

from .models import PaymentRequest, Transaction, Wallet, WithdrawRequest


class WalletSerializer(serializers.ModelSerializer):
    available_balance = serializers.SerializerMethodField()
    user_username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Wallet
        fields = [
            "id",
            "user_username",
            "balance",
            "frozen_balance",
            "withdrawable_balance",
            "available_balance",
            "updated_at",
        ]
        read_only_fields = fields

    def get_available_balance(self, obj):
        return obj.available_balance


class TransactionSerializer(serializers.ModelSerializer):
    tx_type_display = serializers.CharField(source="get_tx_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    order_id = serializers.IntegerField(source="order.id", read_only=True, allow_null=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "tx_type",
            "tx_type_display",
            "status",
            "status_display",
            "amount",
            "balance_before",
            "balance_after",
            "order_id",
            "description",
            "created_at",
        ]
        read_only_fields = fields


class PaymentRequestSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    gateway_display = serializers.CharField(source="get_gateway_display", read_only=True)

    class Meta:
        model = PaymentRequest
        fields = [
            "id",
            "gateway",
            "gateway_display",
            "status",
            "status_display",
            "amount",
            "description",
            "ref_id",
            "order",
            "created_at",
            "paid_at",
        ]
        read_only_fields = fields


class InitiatePaymentSerializer(serializers.Serializer):
    """برای شروع پرداخت زرین‌پال"""
    amount = serializers.DecimalField(max_digits=14, decimal_places=0, min_value=Decimal("10000"))
    description = serializers.CharField(max_length=255, required=False, default="شارژ کیف‌پول")
    callback_url = serializers.URLField()
    order_id = serializers.IntegerField(required=False, allow_null=True)


class AdminDepositSerializer(serializers.Serializer):
    """شارژ دستی توسط ادمین"""
    user_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=0, min_value=Decimal("1000"))
    description = serializers.CharField(max_length=255, required=False, default="")


class WithdrawRequestSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    editor_username = serializers.CharField(source="editor.username", read_only=True)

    class Meta:
        model = WithdrawRequest
        fields = [
            "id",
            "editor_username",
            "amount",
            "status",
            "status_display",
            "bank_name",
            "card_number",
            "iban",
            "account_holder_name",
            "editor_note",
            "admin_note",
            "created_at",
            "paid_at",
        ]
        read_only_fields = [
            "id", "editor_username", "status", "status_display",
            "admin_note", "created_at", "paid_at",
        ]


class CreateWithdrawSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=14, decimal_places=0, min_value=Decimal("50000"))
    bank_name = serializers.CharField(max_length=100)
    card_number = serializers.CharField(max_length=20)
    iban = serializers.CharField(max_length=30, required=False, default="")
    account_holder_name = serializers.CharField(max_length=150)
    editor_note = serializers.CharField(max_length=500, required=False, default="")


class WithdrawReviewSerializer(serializers.Serializer):
    admin_note = serializers.CharField(max_length=500, required=False, default="")
