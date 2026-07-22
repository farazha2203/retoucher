from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from orders.models import Order


User = get_user_model()


class FrontendReadinessPhase15Tests(APITestCase):
    """
    Integration tests for the exact authentication path used by Swagger/frontend.

    These tests intentionally obtain a real JWT from /api/auth/token/ and then
    call the protected timeline endpoint with an Authorization header.
    """

    password = "FrontendPass123!"

    def setUp(self):
        self.owner = User.objects.create_user(
            username="frontend_owner",
            email="frontend-owner@example.com",
            password=self.password,
        )
        self.outsider = User.objects.create_user(
            username="frontend_outsider",
            email="frontend-outsider@example.com",
            password=self.password,
        )
        self.order = Order.objects.create(
            client=self.owner,
            title="Frontend readiness order",
            description="JWT integration test order",
            status=Order.Status.DRAFT,
        )

    def obtain_access_token(self, username):
        response = self.client.post(
            "/api/auth/token/",
            {"username": username, "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        return response.data["access"], response.data["refresh"]

    def test_real_jwt_can_open_owner_timeline(self):
        access, _ = self.obtain_access_token(self.owner.username)

        response = self.client.get(
            f"/api/orders/{self.order.id}/timeline/",
            HTTP_AUTHORIZATION=f"Bearer {access}",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("workflow", response.data)
        self.assertIn("events", response.data)
        self.assertEqual(response.data["workflow"]["workflow_type"], "order")
        self.assertIn("progress_percent", response.data["workflow"])
        self.assertIn("deadline", response.data["workflow"])

    def test_anonymous_timeline_request_is_rejected(self):
        response = self.client.get(f"/api/orders/{self.order.id}/timeline/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unrelated_user_cannot_discover_order(self):
        access, _ = self.obtain_access_token(self.outsider.username)

        response = self.client.get(
            f"/api/orders/{self.order.id}/timeline/",
            HTTP_AUTHORIZATION=f"Bearer {access}",
        )

        # The current queryset intentionally hides other users' orders.
        self.assertIn(
            response.status_code,
            {status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND},
        )

    def test_refresh_token_returns_new_access_token(self):
        _, refresh = self.obtain_access_token(self.owner.username)

        response = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": refresh},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_order_detail_exposes_frontend_workflow_contract(self):
        access, _ = self.obtain_access_token(self.owner.username)

        response = self.client.get(
            f"/api/orders/{self.order.id}/",
            HTTP_AUTHORIZATION=f"Bearer {access}",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("workflow", response.data)

        workflow = response.data["workflow"]
        required_keys = {
            "workflow_type",
            "status",
            "stage",
            "progress_percent",
            "terminal",
            "successful",
            "waiting_for_role",
            "next_action",
            "deadline",
        }
        self.assertTrue(required_keys.issubset(workflow.keys()))
