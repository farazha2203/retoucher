from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import EditorProfile


class AdminUserManagementTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.superuser = User.objects.create_user(
            username="phase532_super",
            password="StrongPass123!",
            role="admin",
            is_staff=True,
            is_superuser=True,
        )
        self.admin = User.objects.create_user(
            username="phase532_admin",
            password="StrongPass123!",
            role="admin",
            is_staff=True,
        )
        self.client_user = User.objects.create_user(
            username="phase532_client",
            password="StrongPass123!",
            role="client",
        )

    def test_superadmin_can_create_editor_and_profile(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse("control_panel:user_create"),
            {
                "username": "created_editor",
                "email": "editor@example.com",
                "first_name": "Editor",
                "last_name": "User",
                "phone_number": "09120000000",
                "role": "editor",
                "is_active": "on",
                "is_verified": "on",
                "is_staff": "",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "editor-display_name": "Created Editor",
                "editor-level": "mid",
                "editor-base_price": "1000",
                "editor-average_delivery_hours": "24",
                "editor-is_available": "on",
                "editor-accepts_direct_requests": "on",
                "editor-accepts_public_requests": "on",
                "editor-accepts_sample_challenges": "on",
                "editor-bio": "",
                "editor-admin_note": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        User = get_user_model()
        user = User.objects.get(username="created_editor")
        self.assertEqual(user.role, "editor")
        self.assertTrue(EditorProfile.objects.filter(user=user).exists())

    def test_admin_can_toggle_client_active_state(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse(
                "control_panel:user_toggle_active",
                args=[self.client_user.pk],
            )
        )
        self.assertEqual(response.status_code, 302)
        self.client_user.refresh_from_db()
        self.assertFalse(self.client_user.is_active)

    def test_client_cannot_open_user_management(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse("control_panel:users"))
        self.assertEqual(response.status_code, 403)

    def test_settings_lists_registered_admin_models(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("control_panel:settings"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "کاربران و ادیتورها")
        self.assertContains(response, "سفارش‌ها و Workflow")
        self.assertContains(response, "مالی و تسویه")
