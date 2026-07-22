from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from orders.models import Order, OrderStatusHistory
from payments.services import settle_order


class _FakeWallet:
    def __init__(self, *, balance=Decimal("10000"), frozen=Decimal("1000")):
        self.balance = balance
        self.frozen_balance = frozen
        self.withdrawable_balance = Decimal("0")

    def deduct_frozen(self, amount):
        self.balance -= amount
        self.frozen_balance -= amount

    def credit_withdrawable(self, amount):
        self.balance += amount
        self.withdrawable_balance += amount

    def refresh_from_db(self):
        return None


class PaymentWorkflowPhase12Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.client_user = User.objects.create_user(
            username="phase12_client",
            password="test-pass",
            role="client",
        )
        self.editor_user = User.objects.create_user(
            username="phase12_editor",
            password="test-pass",
            role="editor",
        )
        self.admin_user = User.objects.create_user(
            username="phase12_admin",
            password="test-pass",
            role="admin",
            is_staff=True,
        )

    def _make_order(self, status):
        return Order.objects.create(
            client=self.client_user,
            editor=self.editor_user,
            title="Phase 1.2 settlement order",
            status=status,
            agreed_price=Decimal("1000"),
            escrow_held=True,
        )

    def _run_settlement(self, order):
        client_wallet = _FakeWallet()
        editor_wallet = _FakeWallet(balance=Decimal("0"), frozen=Decimal("0"))

        commission_setting = Mock()
        commission_setting.commission_percent = Decimal("10")
        commission_setting.calculate.return_value = (
            Decimal("100"),
            Decimal("900"),
        )

        def wallet_for(user):
            if user.pk == self.client_user.pk:
                return client_wallet
            return editor_wallet

        recorded_transactions = [
            SimpleNamespace(id=101),
            SimpleNamespace(id=103),
        ]

        with (
            patch(
                "payments.services.SiteCommissionSetting.get_active",
                return_value=commission_setting,
            ),
            patch(
                "payments.services.get_or_create_wallet",
                side_effect=wallet_for,
            ),
            patch(
                "payments.services._record_transaction",
                side_effect=recorded_transactions,
            ),
            patch(
                "payments.services.Transaction.objects.create",
                return_value=SimpleNamespace(id=102),
            ),
        ):
            result = settle_order(order, admin_user=self.admin_user)

        return result, client_wallet, editor_wallet

    def test_pending_order_moves_to_paid_through_workflow(self):
        order = self._make_order(Order.Status.SETTLEMENT_PENDING)

        result, client_wallet, editor_wallet = self._run_settlement(order)

        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertTrue(order.payment_settled)
        self.assertFalse(order.escrow_held)
        self.assertEqual(order.commission_amount, Decimal("100"))
        self.assertEqual(order.editor_earning, Decimal("900"))
        self.assertIsNotNone(order.paid_at)
        self.assertEqual(result["commission"], Decimal("100"))
        self.assertEqual(client_wallet.balance, Decimal("9000"))
        self.assertEqual(editor_wallet.withdrawable_balance, Decimal("900"))

        history = OrderStatusHistory.objects.get(order=order)
        self.assertEqual(history.from_status, Order.Status.SETTLEMENT_PENDING)
        self.assertEqual(history.to_status, Order.Status.PAID)
        self.assertEqual(history.changed_by, self.admin_user)

    def test_completed_order_records_both_settlement_transitions(self):
        order = self._make_order(Order.Status.COMPLETED)

        self._run_settlement(order)

        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertIsNotNone(order.settlement_started_at)

        transitions = list(
            OrderStatusHistory.objects.filter(order=order)
            .order_by("created_at", "id")
            .values_list("from_status", "to_status")
        )
        self.assertEqual(
            transitions,
            [
                (Order.Status.COMPLETED, Order.Status.SETTLEMENT_PENDING),
                (Order.Status.SETTLEMENT_PENDING, Order.Status.PAID),
            ],
        )

    def test_second_settlement_is_rejected_before_financial_writes(self):
        order = self._make_order(Order.Status.SETTLEMENT_PENDING)
        self._run_settlement(order)

        with (
            patch("payments.services.get_or_create_wallet") as wallet_mock,
            self.assertRaises(ValidationError),
        ):
            settle_order(order, admin_user=self.admin_user)

        wallet_mock.assert_not_called()

    def test_unapproved_status_cannot_be_settled(self):
        order = self._make_order(Order.Status.IN_PROGRESS)

        with (
            patch("payments.services.get_or_create_wallet") as wallet_mock,
            self.assertRaises(ValidationError),
        ):
            settle_order(order, admin_user=self.admin_user)

        wallet_mock.assert_not_called()
