from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from orders.models import Order


class DashboardUnassignedOrderRegressionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(
            username="dashboard_null_editor_admin",
            password="test-pass-123",
            role="admin",
            is_staff=True,
            is_superuser=True,
        )
        self.client_user = User.objects.create_user(
            username="dashboard_null_editor_client",
            password="test-pass-123",
            role="client",
        )
        self.order = Order.objects.create(
            client=self.client_user,
            editor=None,
            title="سفارش بدون ادیتور",
            status=Order.Status.SUBMITTED,
        )

    def test_admin_dashboard_renders_order_without_editor(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("control_panel:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "سفارش بدون ادیتور")
        self.assertContains(response, "تخصیص‌نیافته")

    def test_client_dashboard_renders_own_order_without_editor(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse("control_panel:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "سفارش بدون ادیتور")
        self.assertContains(response, "تخصیص‌نیافته")
