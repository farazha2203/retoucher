from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import (
    EditorPortfolioItem,
    EditorProfile,
    PortfolioComment,
    PortfolioCommentReport,
    PortfolioLike,
)


class PortfolioSocialPhase537Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.client_user = User.objects.create_user(
            username="phase537_client",
            password="StrongPass123!",
            role="client",
        )
        self.editor_user = User.objects.create_user(
            username="phase537_editor",
            password="StrongPass123!",
            role="editor",
        )
        self.profile = EditorProfile.objects.create(
            user=self.editor_user,
            display_name="Phase 537 Editor",
        )
        self.item = EditorPortfolioItem.objects.create(
            editor=self.profile,
            title="Before After",
            is_active=True,
        )

    def test_like_toggle_is_unique(self):
        api = APIClient()
        api.force_authenticate(self.client_user)
        url = f"/api/accounts/portfolio/{self.item.pk}/toggle_like/"

        first = api.post(url)
        self.assertEqual(first.status_code, 200)
        self.assertTrue(first.data["liked"])
        self.assertEqual(PortfolioLike.objects.count(), 1)

        second = api.post(url)
        self.assertEqual(second.status_code, 200)
        self.assertFalse(second.data["liked"])
        self.assertEqual(PortfolioLike.objects.count(), 0)

    def test_comment_is_pending_until_moderation(self):
        api = APIClient()
        api.force_authenticate(self.client_user)
        response = api.post(
            f"/api/accounts/portfolio/{self.item.pk}/comment/",
            {"body": "نمونه‌کار بسیار خوبی بود."},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            PortfolioComment.objects.get().status,
            PortfolioComment.Status.PENDING,
        )

    def test_report_is_unique_per_user(self):
        comment = PortfolioComment.objects.create(
            portfolio_item=self.item,
            user=self.editor_user,
            body="دیدگاه",
            status=PortfolioComment.Status.APPROVED,
        )
        api = APIClient()
        api.force_authenticate(self.client_user)
        url = f"/api/accounts/portfolio/{self.item.pk}/report-comment/"

        first = api.post(
            url,
            {"comment": comment.pk, "reason": "محتوای نامناسب"},
            format="json",
        )
        second = api.post(
            url,
            {"comment": comment.pk, "reason": "تکرار گزارش"},
            format="json",
        )
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(PortfolioCommentReport.objects.count(), 1)
