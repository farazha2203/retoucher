from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import Order
from payments.models import SiteCommissionSetting, Transaction, Wallet


User = get_user_model()


class SettlementAdminAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_user",
            email="admin@example.com",
            password="pass123456",
            role="admin",
            is_staff=True,
            is_superuser=True,
        )
        self.support = User.objects.create_user(
            username="support_user",
            email="support@example.com",
            password="pass123456",
            role="support",
            is_staff=True,
        )
        self.client_user = User.objects.create_user(
            username="client_user",
            email="client@example.com",
            password="pass123456",
            role="client",
        )
        self.editor = User.objects.create_user(
            username="editor_user",
            email="editor@example.com",
            password="pass123456",
            role="editor",
        )

        SiteCommissionSetting.objects.create(
            commission_percent=Decimal("10.00"),
            min_commission=Decimal("0"),
            is_active=True,
            created_by=self.admin,
        )

        self.client_wallet = Wallet.objects.create(
            user=self.client_user,
            balance=Decimal("1000000"),
            frozen_balance=Decimal("300000"),
            withdrawable_balance=Decimal("0"),
        )
        self.editor_wallet = Wallet.objects.create(
            user=self.editor,
            balance=Decimal("0"),
            frozen_balance=Decimal("0"),
            withdrawable_balance=Decimal("0"),
        )

        self.order = Order.objects.create(
            client=self.client_user,
            editor=self.editor,
            title="Settlement Test Order",
            description="Test order for settlement",
            status=Order.Status.SETTLEMENT_PENDING,
            agreed_price=Decimal("300000"),
            escrow_held=True,
            payment_settled=False,
        )

    def authenticate_admin(self):
        self.client.force_authenticate(user=self.admin)

    def authenticate_support(self):
        self.client.force_authenticate(user=self.support)

    def authenticate_client(self):
        self.client.force_authenticate(user=self.client_user)

    def test_admin_can_view_settlement_summary(self):
        self.authenticate_admin()

        response = self.client.get(reverse("settlement-settlement-summary"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_support_can_view_settlement_summary(self):
        self.authenticate_support()

        response = self.client.get(reverse("settlement-settlement-summary"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_admin_cannot_view_settlement_summary(self):
        self.authenticate_client()

        response = self.client.get(reverse("settlement-settlement-summary"))

        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED],
        )

    def test_admin_can_view_pending_settlements(self):
        self.authenticate_admin()

        response = self.client.get(reverse("settlement-list-pending"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_view_all_settlements(self):
        self.authenticate_admin()

        response = self.client.get(reverse("settlement-list-all"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_view_order_settlement_detail(self):
        self.authenticate_admin()

        response = self.client.get(
            reverse("settlement-order-detail", args=[self.order.id])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_set_agreed_price(self):
        self.authenticate_admin()

        response = self.client.post(
            reverse("settlement-set-agreed-price", args=[self.order.id]),
            {
                "agreed_price": "400000",
                "note": "Updated settlement price",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.order.refresh_from_db()
        self.assertEqual(self.order.agreed_price, Decimal("400000"))

    def test_non_admin_cannot_set_agreed_price(self):
        self.authenticate_client()

        response = self.client.post(
            reverse("settlement-set-agreed-price", args=[self.order.id]),
            {
                "agreed_price": "400000",
                "note": "Invalid attempt",
            },
            format="json",
        )

        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED],
        )

    def test_cannot_set_invalid_agreed_price(self):
        self.authenticate_admin()

        response = self.client.post(
            reverse("settlement-set-agreed-price", args=[self.order.id]),
            {
                "agreed_price": "0",
                "note": "Invalid price",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_settle_without_editor(self):
        self.authenticate_admin()

        order = Order.objects.create(
            client=self.client_user,
            editor=None,
            title="No Editor Order",
            status=Order.Status.SETTLEMENT_PENDING,
            agreed_price=Decimal("100000"),
            escrow_held=True,
            payment_settled=False,
        )

        response = self.client.post(
            reverse("settlement-settle", args=[order.id]),
            {"note": "Try settle without editor"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_settle_without_agreed_price(self):
        self.authenticate_admin()

        self.order.agreed_price = Decimal("0")
        self.order.save(update_fields=["agreed_price"])

        response = self.client.post(
            reverse("settlement-settle", args=[self.order.id]),
            {"note": "Try settle without price"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_can_settle_order(self):
        self.authenticate_admin()

        response = self.client.post(
            reverse("settlement-settle", args=[self.order.id]),
            {"note": "Final settlement"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.order.refresh_from_db()
        self.client_wallet.refresh_from_db()
        self.editor_wallet.refresh_from_db()

        self.assertTrue(self.order.payment_settled)
        self.assertFalse(self.order.escrow_held)
        self.assertEqual(self.order.commission_amount, Decimal("30000"))
        self.assertEqual(self.order.editor_earning, Decimal("270000"))

        self.assertTrue(
            Transaction.objects.filter(
                order=self.order,
                tx_type=Transaction.TxType.COMMISSION,
                status=Transaction.Status.SUCCESS,
            ).exists()
        )
        self.assertTrue(
            Transaction.objects.filter(
                order=self.order,
                tx_type=Transaction.TxType.EDITOR_EARNING,
                status=Transaction.Status.SUCCESS,
            ).exists()
        )

    def test_cannot_settle_twice(self):
        self.authenticate_admin()

        first_response = self.client.post(
            reverse("settlement-settle", args=[self.order.id]),
            {"note": "First settlement"},
            format="json",
        )

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)

        second_response = self.client.post(
            reverse("settlement-settle", args=[self.order.id]),
            {"note": "Second settlement"},
            format="json",
        )

        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)