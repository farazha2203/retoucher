from django.contrib.auth import get_user_model
from django.test import TestCase

from control_panel.dashboard_engine import build_dashboard_context


class DashboardEngineRoleTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.users = {
            role: User.objects.create_user(
                username=f"dashboard_{role}",
                password="test-pass-123",
                role=role,
                is_staff=(role == "admin"),
            )
            for role in [
                "client",
                "editor",
                "support",
                "supervisor",
                "admin",
            ]
        }

    def test_role_specific_dashboard_kinds(self):
        for role, user in self.users.items():
            context = build_dashboard_context(user)
            self.assertEqual(context["dashboard_kind"], role)
            self.assertTrue(context["primary_kpis"])
            self.assertIn("status_labels", context)
            self.assertIn("month_values", context)

    def test_client_does_not_receive_admin_metrics(self):
        context = build_dashboard_context(self.users["client"])
        self.assertNotIn("open_disputes", context)
        self.assertEqual(context["page_title"], "داشبورد مشتری")

    def test_editor_receives_editor_metrics(self):
        context = build_dashboard_context(self.users["editor"])
        self.assertIn("total_earnings", context)
        self.assertIn("delivery_due_count", context)

    def test_admin_receives_operational_metrics(self):
        context = build_dashboard_context(self.users["admin"])
        self.assertIn("commission_volume", context)
        self.assertIn("open_disputes", context)
