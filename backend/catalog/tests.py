from django.core.management import call_command
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import EditCategory, EditPackage, EditStyle


class CatalogAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.category = EditCategory.objects.create(
            title="Beauty Retouch",
            slug="beauty-retouch",
            description="Beauty edit category",
            sort_order=1,
        )

        self.style = EditStyle.objects.create(
            category=self.category,
            title="Natural Beauty",
            slug="natural-beauty",
            description="Natural retouch style",
            min_price=100000,
            max_price=500000,
            suggested_price=250000,
            estimated_delivery_hours=24,
            sort_order=1,
        )

        self.package = EditPackage.objects.create(
            style=self.style,
            title="Standard",
            level=EditPackage.PackageLevel.STANDARD,
            description="Standard package",
            price=250000,
            min_images=1,
            max_images=3,
            estimated_delivery_hours=24,
            revision_count=2,
            sort_order=1,
        )

    def test_list_categories_with_nested_styles_and_packages(self):
        response = self.client.get("/api/catalog/categories/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["slug"], "beauty-retouch")
        self.assertEqual(len(response.data[0]["styles"]), 1)
        self.assertEqual(response.data[0]["styles"][0]["slug"], "natural-beauty")
        self.assertEqual(len(response.data[0]["styles"][0]["packages"]), 1)

    def test_retrieve_category_by_slug(self):
        response = self.client.get("/api/catalog/categories/beauty-retouch/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Beauty Retouch")

    def test_list_styles_can_filter_by_category(self):
        response = self.client.get("/api/catalog/styles/?category=beauty-retouch")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["slug"], "natural-beauty")

    def test_list_packages_can_filter_by_style(self):
        response = self.client.get("/api/catalog/packages/?style=natural-beauty")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Standard")

    def test_inactive_category_is_hidden(self):
        self.category.is_active = False
        self.category.save(update_fields=["is_active"])

        response = self.client.get("/api/catalog/categories/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


class CatalogDemoDataCommandTests(TestCase):
    def test_create_catalog_demo_data_command(self):
        call_command("create_catalog_demo_data")

        self.assertGreater(EditCategory.objects.count(), 0)
        self.assertGreater(EditStyle.objects.count(), 0)
        self.assertGreater(EditPackage.objects.count(), 0)

class CatalogInactiveNestedItemsHiddenTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.category = EditCategory.objects.create(
            title="Portrait",
            slug="portrait",
            sort_order=1,
        )
        self.active_style = EditStyle.objects.create(
            category=self.category,
            title="Active Style",
            slug="active-style",
            sort_order=1,
        )
        self.inactive_style = EditStyle.objects.create(
            category=self.category,
            title="Inactive Style",
            slug="inactive-style",
            sort_order=2,
            is_active=False,
        )
        self.active_package = EditPackage.objects.create(
            style=self.active_style,
            title="Active Package",
            price=100000,
            sort_order=1,
        )
        self.inactive_package = EditPackage.objects.create(
            style=self.active_style,
            title="Inactive Package",
            price=100000,
            sort_order=2,
            is_active=False,
        )

    def test_inactive_style_hidden_inside_category(self):
        response = self.client.get(f"/api/catalog/categories/{self.category.slug}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        style_slugs = [s["slug"] for s in response.data["styles"]]
        self.assertIn("active-style", style_slugs)
        self.assertNotIn("inactive-style", style_slugs)

    def test_inactive_package_hidden_inside_style(self):
        response = self.client.get(f"/api/catalog/styles/{self.active_style.slug}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        package_titles = [p["title"] for p in response.data["packages"]]
        self.assertIn("Active Package", package_titles)
        self.assertNotIn("Inactive Package", package_titles)