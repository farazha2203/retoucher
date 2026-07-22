from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from payments import services
from payments.models import (
    PaymentRequest,
    SiteCommissionSetting,
    Transaction,
    Wallet,
    WithdrawRequest,
)


User = get_user_model()


class PaymentServiceTests(TestCase):
    def create_user(self, username, role=None):
        user = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="test-pass-123",
        )

        if role and any(field.name == "role" for field in User._meta.fields):
            user.role = role
            user.save(update_fields=["role"])

        return user

    def setUp(self):
        self.admin_user = self.create_user("admin-user", role="admin")
        self.client_user = self.create_user("client-user", role="client")
        self.editor_user = self.create_user("editor-user", role="editor")

    def test_get_or_create_wallet_creates_default_wallet(self):
        wallet = services.get_or_create_wallet(self.client_user)

        self.assertIsInstance(wallet, Wallet)
        self.assertEqual(wallet.user, self.client_user)
        self.assertEqual(wallet.balance, Decimal("0"))
        self.assertEqual(wallet.frozen_balance, Decimal("0"))
        self.assertEqual(wallet.withdrawable_balance, Decimal("0"))
        self.assertEqual(wallet.available_balance, Decimal("0"))

    def test_admin_deposit_increases_wallet_balance_and_creates_transaction(self):
        tx = services.admin_deposit(
            user=self.client_user,
            amount=Decimal("150000"),
            admin_user=self.admin_user,
            description="Test admin deposit",
        )

        wallet = Wallet.objects.get(user=self.client_user)

        self.assertEqual(wallet.balance, Decimal("150000"))
        self.assertEqual(wallet.frozen_balance, Decimal("0"))
        self.assertEqual(wallet.withdrawable_balance, Decimal("0"))

        self.assertEqual(tx.wallet, wallet)
        self.assertEqual(tx.tx_type, Transaction.TxType.DEPOSIT)
        self.assertEqual(tx.status, Transaction.Status.SUCCESS)
        self.assertEqual(tx.amount, Decimal("150000"))
        self.assertEqual(tx.balance_before, Decimal("0"))
        self.assertEqual(tx.balance_after, Decimal("150000"))
        self.assertEqual(tx.created_by, self.admin_user)

    def test_admin_deposit_rejects_non_positive_amount(self):
        with self.assertRaises(ValidationError):
            services.admin_deposit(
                user=self.client_user,
                amount=Decimal("0"),
                admin_user=self.admin_user,
            )

        with self.assertRaises(ValidationError):
            services.admin_deposit(
                user=self.client_user,
                amount=Decimal("-1000"),
                admin_user=self.admin_user,
            )

    def test_request_withdrawal_creates_pending_request_without_deducting_wallet(self):
        wallet = services.get_or_create_wallet(self.editor_user)
        wallet.credit_withdrawable(Decimal("200000"))

        withdraw = services.request_withdrawal(
            editor=self.editor_user,
            amount=Decimal("50000"),
            bank_info={
                "bank_name": "Test Bank",
                "card_number": "1234567890123456",
                "iban": "IR123456789",
                "account_holder_name": "Editor User",
            },
        )

        wallet.refresh_from_db()

        self.assertEqual(withdraw.editor, self.editor_user)
        self.assertEqual(withdraw.amount, Decimal("50000"))
        self.assertEqual(withdraw.status, WithdrawRequest.Status.PENDING)

        # در مرحله request هنوز پول کم نمی‌شود.
        self.assertEqual(wallet.balance, Decimal("200000"))
        self.assertEqual(wallet.withdrawable_balance, Decimal("200000"))

    def test_request_withdrawal_rejects_insufficient_balance(self):
        services.get_or_create_wallet(self.editor_user)

        with self.assertRaises(ValidationError):
            services.request_withdrawal(
                editor=self.editor_user,
                amount=Decimal("100000"),
                bank_info={},
            )

    def test_request_withdrawal_rejects_non_positive_amount(self):
        wallet = services.get_or_create_wallet(self.editor_user)
        wallet.credit_withdrawable(Decimal("200000"))

        with self.assertRaises(ValidationError):
            services.request_withdrawal(
                editor=self.editor_user,
                amount=Decimal("0"),
                bank_info={},
            )

        with self.assertRaises(ValidationError):
            services.request_withdrawal(
                editor=self.editor_user,
                amount=Decimal("-1000"),
                bank_info={},
            )

    def test_approve_withdrawal_deducts_withdrawable_balance_and_creates_transaction(self):
        wallet = services.get_or_create_wallet(self.editor_user)
        wallet.credit_withdrawable(Decimal("200000"))

        withdraw = services.request_withdrawal(
            editor=self.editor_user,
            amount=Decimal("50000"),
            bank_info={},
        )

        tx = services.approve_withdrawal(
            withdraw_request=withdraw,
            admin_user=self.admin_user,
        )

        wallet.refresh_from_db()
        withdraw.refresh_from_db()

        self.assertEqual(withdraw.status, WithdrawRequest.Status.APPROVED)
        self.assertEqual(withdraw.reviewed_by, self.admin_user)
        self.assertIsNotNone(withdraw.reviewed_at)

        self.assertEqual(wallet.balance, Decimal("150000"))
        self.assertEqual(wallet.withdrawable_balance, Decimal("150000"))

        self.assertEqual(tx.wallet, wallet)
        self.assertEqual(tx.tx_type, Transaction.TxType.WITHDRAWAL)
        self.assertEqual(tx.status, Transaction.Status.SUCCESS)
        self.assertEqual(tx.amount, Decimal("50000"))
        self.assertEqual(tx.balance_before, Decimal("200000"))
        self.assertEqual(tx.balance_after, Decimal("150000"))

    def test_approve_withdrawal_only_allows_pending_requests(self):
        wallet = services.get_or_create_wallet(self.editor_user)
        wallet.credit_withdrawable(Decimal("200000"))

        withdraw = services.request_withdrawal(
            editor=self.editor_user,
            amount=Decimal("50000"),
            bank_info={},
        )

        services.approve_withdrawal(withdraw, admin_user=self.admin_user)

        with self.assertRaises(ValidationError):
            services.approve_withdrawal(withdraw, admin_user=self.admin_user)

    def test_reject_withdrawal_marks_pending_request_as_rejected_without_deducting_wallet(self):
        wallet = services.get_or_create_wallet(self.editor_user)
        wallet.credit_withdrawable(Decimal("200000"))

        withdraw = services.request_withdrawal(
            editor=self.editor_user,
            amount=Decimal("50000"),
            bank_info={},
        )

        services.reject_withdrawal(
            withdraw_request=withdraw,
            admin_user=self.admin_user,
            note="Rejected in test",
        )

        wallet.refresh_from_db()
        withdraw.refresh_from_db()

        self.assertEqual(withdraw.status, WithdrawRequest.Status.REJECTED)
        self.assertEqual(withdraw.reviewed_by, self.admin_user)
        self.assertIsNotNone(withdraw.reviewed_at)
        self.assertEqual(withdraw.admin_note, "Rejected in test")

        self.assertEqual(wallet.balance, Decimal("200000"))
        self.assertEqual(wallet.withdrawable_balance, Decimal("200000"))

    def test_reject_withdrawal_only_allows_pending_requests(self):
        wallet = services.get_or_create_wallet(self.editor_user)
        wallet.credit_withdrawable(Decimal("200000"))

        withdraw = services.request_withdrawal(
            editor=self.editor_user,
            amount=Decimal("50000"),
            bank_info={},
        )

        services.approve_withdrawal(withdraw, admin_user=self.admin_user)

        with self.assertRaises(ValidationError):
            services.reject_withdrawal(
                withdraw_request=withdraw,
                admin_user=self.admin_user,
            )

    def test_mark_withdrawal_paid_only_allows_approved_requests(self):
        wallet = services.get_or_create_wallet(self.editor_user)
        wallet.credit_withdrawable(Decimal("200000"))

        withdraw = services.request_withdrawal(
            editor=self.editor_user,
            amount=Decimal("50000"),
            bank_info={},
        )

        with self.assertRaises(ValidationError):
            services.mark_withdrawal_paid(
                withdraw_request=withdraw,
                admin_user=self.admin_user,
            )

        services.approve_withdrawal(withdraw, admin_user=self.admin_user)
        services.mark_withdrawal_paid(withdraw, admin_user=self.admin_user)

        withdraw.refresh_from_db()

        self.assertEqual(withdraw.status, WithdrawRequest.Status.PAID)
        self.assertIsNotNone(withdraw.paid_at)
        self.assertIn(self.admin_user.username, withdraw.admin_note)

    def test_payment_request_defaults(self):
        payment_request = PaymentRequest.objects.create(
            user=self.client_user,
            amount=Decimal("250000"),
            description="Test payment request",
        )

        self.assertEqual(payment_request.gateway, PaymentRequest.Gateway.ZARINPAL)
        self.assertEqual(payment_request.status, PaymentRequest.Status.CREATED)
        self.assertEqual(payment_request.amount, Decimal("250000"))
        self.assertEqual(payment_request.user, self.client_user)

    def test_site_commission_calculation(self):
        setting = SiteCommissionSetting.objects.create(
            commission_percent=Decimal("10.00"),
            min_commission=Decimal("0"),
            is_active=True,
            created_by=self.admin_user,
        )

        commission, editor_earning = setting.calculate(Decimal("200000"))

        self.assertEqual(commission, Decimal("20000"))
        self.assertEqual(editor_earning, Decimal("180000"))

    def test_site_commission_respects_min_commission(self):
        setting = SiteCommissionSetting.objects.create(
            commission_percent=Decimal("1.00"),
            min_commission=Decimal("10000"),
            is_active=True,
            created_by=self.admin_user,
        )

        commission, editor_earning = setting.calculate(Decimal("200000"))

        self.assertEqual(commission, Decimal("10000"))
        self.assertEqual(editor_earning, Decimal("190000"))