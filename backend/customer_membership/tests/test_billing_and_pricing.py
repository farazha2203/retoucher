from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from customer_membership.billing import purchase_membership
from customer_membership.models import CustomerProfile, CustomerTier
from payments.models import Transaction, Wallet


class MembershipBillingTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="studio_test",
            password="StrongPass123!",
            role="client",
        )
        self.profile = CustomerProfile.objects.create(user=self.user)
        self.tier = CustomerTier.objects.create(
            code="studio",
            title="Studio",
            discount_percent=10,
            monthly_price=100000,
            annual_price=1000000,
            is_purchasable=True,
        )
        self.wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal("500000"),
        )

    def test_wallet_purchase(self):
        sub = purchase_membership(
            user=self.user,
            tier=self.tier,
            period="monthly",
        )
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("400000"))
        self.assertEqual(sub.status, "active")
        self.assertEqual(Transaction.objects.count(), 1)

    def test_purchase_api(self):
        api = APIClient()
        api.force_authenticate(self.user)
        response = api.post(
            "/api/customer/membership/purchase/",
            {"tier_id": self.tier.pk, "period": "monthly"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
