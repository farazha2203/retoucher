from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import EditorPortfolioItem, EditorProfile

GIF = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"

class PortfolioManagementPhase539Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.editor = User.objects.create_user(username="e1", password="StrongPass123!", role="editor")
        self.other = User.objects.create_user(username="e2", password="StrongPass123!", role="editor")
        self.admin = User.objects.create_user(username="a1", password="StrongPass123!", role="admin", is_staff=True)
        self.profile = EditorProfile.objects.create(user=self.editor, display_name="Editor")
        EditorProfile.objects.create(user=self.other, display_name="Other")
        self.item = EditorPortfolioItem.objects.create(
            editor=self.profile,
            title="Draft",
            before_image=SimpleUploadedFile("before.gif", GIF, content_type="image/gif"),
            after_image=SimpleUploadedFile("after.gif", GIF, content_type="image/gif"),
            review_status=EditorPortfolioItem.ReviewStatus.DRAFT,
            is_active=False,
        )

    def test_owner_can_submit(self):
        api = APIClient(); api.force_authenticate(self.editor)
        response = api.post(f"/api/accounts/editors/me/portfolio/{self.item.pk}/submit/")
        self.assertEqual(response.status_code, 200)

    def test_other_editor_cannot_edit(self):
        api = APIClient(); api.force_authenticate(self.other)
        response = api.patch(f"/api/accounts/editors/me/portfolio/{self.item.pk}/", {"title": "Hack"}, format="json")
        self.assertEqual(response.status_code, 404)

    def test_admin_can_approve(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("control_panel:review_portfolio_item", args=[self.item.pk]), {"action": "approve"})
        self.assertEqual(response.status_code, 302)
        self.item.refresh_from_db()
        self.assertTrue(self.item.is_active)
