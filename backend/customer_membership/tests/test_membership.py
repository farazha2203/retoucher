from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from customer_membership.models import CustomerProfile, CustomerTier, PerformanceCommissionRule
from customer_membership.pricing import calculate_order_pricing


class MembershipTests(TestCase):
    def setUp(self):
        User=get_user_model()
        self.user=User.objects.create_user(username="client540", password="StrongPass123!", role="client")
        self.tier=CustomerTier.objects.create(code="studio", title="Studio", discount_percent=10, priority_level=10)
        CustomerProfile.objects.create(user=self.user, tier=self.tier)

    def test_profile_update(self):
        api=APIClient(); api.force_authenticate(self.user)
        response=api.patch("/api/customer/profile/me/", {"national_id":"1234567890","landline":"03132223344","occupation":"آتلیه‌دار","city":"اصفهان","address":"خیابان نمونه"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["profile_completed"])

    def test_discount(self):
        result=calculate_order_pricing(base_price=Decimal("200000"), client=self.user)
        self.assertEqual(result["final_price"], Decimal("180000"))
