from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import EditorPortfolioItem, EditorProfile
from catalog.models import EditCategory, EditStyle

User = get_user_model()


class RegisterAndMeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/accounts/register/"

    def valid_payload(self, **overrides):
        payload = {
            "username": "newclient",
            "email": "newclient@example.com",
            "password": "Str0ng!Passw0rd",
            "password_confirm": "Str0ng!Passw0rd",
            "role": "client",
        }
        payload.update(overrides)
        return payload

    def test_register_success(self):
        response = self.client.post(self.url, self.valid_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newclient").exists())
        user = User.objects.get(username="newclient")
        self.assertTrue(user.check_password("Str0ng!Passw0rd"))
        # پاسخ نباید پسورد رو برگردونه
        self.assertNotIn("password", response.data)

    def test_register_password_mismatch(self):
        response = self.client.post(
            self.url,
            self.valid_payload(password_confirm="Different1!"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password_confirm", response.data)

    def test_register_weak_password_rejected(self):
        response = self.client.post(
            self.url,
            self.valid_payload(password="12345678", password_confirm="12345678"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_register_cannot_escalate_role_to_admin(self):
        response = self.client.post(
            self.url,
            self.valid_payload(username="hacker", role="admin"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("role", response.data)

    def test_me_requires_authentication(self):
        response = self.client.get("/api/accounts/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_current_user(self):
        user = User.objects.create_user(
            username="clientuser", password="Str0ng!Passw0rd"
        )
        self.client.force_authenticate(user=user)
        response = self.client.get("/api/accounts/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "clientuser")


class InactivePortfolioItemHiddenTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        category = EditCategory.objects.create(title="Beauty", slug="beauty", sort_order=1)
        self.style = EditStyle.objects.create(
            category=category,
            title="Natural",
            slug="natural",
            min_price=100000,
            max_price=500000,
            suggested_price=250000,
        )
        user = User.objects.create_user(username="editor_x", password="pass12345")
        self.profile = EditorProfile.objects.create(
            user=user, display_name="Editor X", is_available=True
        )
        EditorPortfolioItem.objects.create(
            editor=self.profile, style=self.style, title="Active item", is_active=True
        )
        EditorPortfolioItem.objects.create(
            editor=self.profile, style=self.style, title="Hidden item", is_active=False
        )

    def test_inactive_item_not_in_detail(self):
        response = self.client.get(f"/api/accounts/editors/{self.profile.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [item["title"] for item in response.data["portfolio_items"]]
        self.assertIn("Active item", titles)
        self.assertNotIn("Hidden item", titles)