from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import EditorPortfolioItem, EditorProfile
from catalog.models import EditCategory, EditStyle


class EditorProfileAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        User = get_user_model()

        self.category = EditCategory.objects.create(
            title="Beauty Retouch",
            slug="beauty-retouch",
            sort_order=1,
        )
        self.style = EditStyle.objects.create(
            category=self.category,
            title="Natural Beauty",
            slug="natural-beauty",
            min_price=100000,
            max_price=500000,
            suggested_price=250000,
            estimated_delivery_hours=24,
        )

        self.user = User.objects.create_user(
            username="editor_test",
            password="EditorPass123!",
            email="editor_test@example.com",
        )

        self.profile = EditorProfile.objects.create(
            user=self.user,
            display_name="Test Editor",
            bio="Test editor bio",
            level=EditorProfile.EditorLevel.SENIOR,
            base_price=250000,
            average_delivery_hours=24,
            rating_average=4.50,
            completed_orders_count=10,
            is_available=True,
        )
        self.profile.skills.add(self.style)

        EditorPortfolioItem.objects.create(
            editor=self.profile,
            style=self.style,
            title="Beauty sample",
            description="Sample work",
            is_featured=True,
        )

    def test_list_editors(self):
        response = self.client.get("/api/accounts/editors/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["display_name"], "Test Editor")
        self.assertEqual(response.data[0]["skills"][0]["slug"], "natural-beauty")

    def test_retrieve_editor_detail_includes_portfolio(self):
        response = self.client.get(f"/api/accounts/editors/{self.profile.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["display_name"], "Test Editor")
        self.assertEqual(len(response.data["portfolio_items"]), 1)

    def test_filter_editors_by_skill(self):
        response = self.client.get("/api/accounts/editors/?skill=natural-beauty")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_unavailable_editor_is_hidden(self):
        self.profile.is_available = False
        self.profile.save(update_fields=["is_available"])

        response = self.client.get("/api/accounts/editors/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


class EditorDemoDataCommandTests(TestCase):
    def test_create_editor_demo_data_command(self):
        call_command("create_catalog_demo_data")
        call_command("create_editor_demo_data")

        self.assertGreater(EditorProfile.objects.count(), 0)
        self.assertGreater(EditorPortfolioItem.objects.count(), 0)