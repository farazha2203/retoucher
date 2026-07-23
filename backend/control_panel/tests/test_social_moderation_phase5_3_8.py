from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class SocialModerationPanelTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(
            username="phase538_admin",
            password="StrongPass123!",
            role="admin",
            is_staff=True,
        )
        self.client_user = User.objects.create_user(
            username="phase538_client",
            password="StrongPass123!",
            role="client",
        )

    def test_admin_can_open_moderation_panel(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("control_panel:social_moderation"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "مدیریت لایک و دیدگاه نمونه‌کارها")

    def test_client_cannot_open_moderation_panel(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse("control_panel:social_moderation"))
        self.assertEqual(response.status_code, 403)
