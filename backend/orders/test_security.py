import shutil
import tempfile
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone

from rest_framework import status as drf_status
from rest_framework.test import APITestCase

from .models import (
    Order,
    OrderComment,
    OrderDelivery,
    OrderImage,
    OrderNotification,
)


TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class OrderPermissionSecurityAuditTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        User = get_user_model()

        self.client_user = User.objects.create_user(
            username="client_security",
            password="ClientPass123!",
            role="client",
        )
        self.other_client_user = User.objects.create_user(
            username="other_client_security",
            password="ClientPass123!",
            role="client",
        )
        self.editor_user = User.objects.create_user(
            username="editor_security",
            password="EditorPass123!",
            role="editor",
        )
        self.other_editor_user = User.objects.create_user(
            username="other_editor_security",
            password="EditorPass123!",
            role="editor",
        )
        self.support_user = User.objects.create_user(
            username="support_security",
            password="SupportPass123!",
            role="support",
            is_staff=True,
        )

        self.order = Order.objects.create(
            client=self.client_user,
            editor=self.editor_user,
            title="Security audit order",
            description="Order used for permission audit tests.",
            deadline=timezone.now() + timedelta(days=5),
        )

        self.other_order = Order.objects.create(
            client=self.other_client_user,
            editor=self.other_editor_user,
            title="Other security audit order",
            description="Another user's order.",
            deadline=timezone.now() + timedelta(days=5),
        )

        self.image = OrderImage.objects.create(
            order=self.order,
            image=SimpleUploadedFile(
                "security-original.jpg",
                b"fake image content",
                content_type="image/jpeg",
            ),
            note="Security original image",
        )

        self.other_image = OrderImage.objects.create(
            order=self.other_order,
            image=SimpleUploadedFile(
                "other-security-original.jpg",
                b"fake other image content",
                content_type="image/jpeg",
            ),
            note="Other security original image",
        )

        self.delivery = OrderDelivery.objects.create(
            order=self.order,
            file=SimpleUploadedFile(
                "security-delivery.txt",
                b"fake delivery content",
                content_type="text/plain",
            ),
            note="Security delivery file",
            uploaded_by=self.editor_user,
        )

        self.other_delivery = OrderDelivery.objects.create(
            order=self.other_order,
            file=SimpleUploadedFile(
                "other-security-delivery.txt",
                b"fake other delivery content",
                content_type="text/plain",
            ),
            note="Other security delivery file",
            uploaded_by=self.other_editor_user,
        )

    def authenticate_as_client(self):
        self.client.force_authenticate(user=self.client_user)

    def authenticate_as_other_client(self):
        self.client.force_authenticate(user=self.other_client_user)

    def authenticate_as_editor(self):
        self.client.force_authenticate(user=self.editor_user)

    def authenticate_as_other_editor(self):
        self.client.force_authenticate(user=self.other_editor_user)

    def authenticate_as_support(self):
        self.client.force_authenticate(user=self.support_user)

    def get_list_items(self, response):
        """
        Supports both paginated and non-paginated DRF responses.
        """
        if isinstance(response.data, dict) and "results" in response.data:
            return response.data["results"]
        return response.data

    def assert_forbidden_or_not_found(self, response):
        self.assertIn(
            response.status_code,
            (
                drf_status.HTTP_403_FORBIDDEN,
                drf_status.HTTP_404_NOT_FOUND,
            ),
        )

    def test_anonymous_user_cannot_access_orders(self):
        list_response = self.client.get("/api/orders/")
        self.assertIn(
            list_response.status_code,
            (
                drf_status.HTTP_401_UNAUTHORIZED,
                drf_status.HTTP_403_FORBIDDEN,
            ),
        )

        detail_response = self.client.get(f"/api/orders/{self.order.id}/")
        self.assertIn(
            detail_response.status_code,
            (
                drf_status.HTTP_401_UNAUTHORIZED,
                drf_status.HTTP_403_FORBIDDEN,
            ),
        )

    def test_client_can_only_list_and_access_own_orders(self):
        self.authenticate_as_client()

        list_response = self.client.get("/api/orders/")
        self.assertEqual(list_response.status_code, drf_status.HTTP_200_OK)

        items = self.get_list_items(list_response)
        order_ids = {item["id"] for item in items}

        self.assertIn(self.order.id, order_ids)
        self.assertNotIn(self.other_order.id, order_ids)

        own_detail_response = self.client.get(f"/api/orders/{self.order.id}/")
        self.assertEqual(own_detail_response.status_code, drf_status.HTTP_200_OK)

        other_detail_response = self.client.get(f"/api/orders/{self.other_order.id}/")
        self.assert_forbidden_or_not_found(other_detail_response)

    def test_editor_can_only_list_and_access_assigned_orders(self):
        self.authenticate_as_editor()

        list_response = self.client.get("/api/orders/")
        self.assertEqual(list_response.status_code, drf_status.HTTP_200_OK)

        items = self.get_list_items(list_response)
        order_ids = {item["id"] for item in items}

        self.assertIn(self.order.id, order_ids)
        self.assertNotIn(self.other_order.id, order_ids)

        own_detail_response = self.client.get(f"/api/orders/{self.order.id}/")
        self.assertEqual(own_detail_response.status_code, drf_status.HTTP_200_OK)

        other_detail_response = self.client.get(f"/api/orders/{self.other_order.id}/")
        self.assert_forbidden_or_not_found(other_detail_response)

    def test_support_can_access_multiple_orders(self):
        self.authenticate_as_support()

        list_response = self.client.get("/api/orders/")
        self.assertEqual(list_response.status_code, drf_status.HTTP_200_OK)

        items = self.get_list_items(list_response)
        order_ids = {item["id"] for item in items}

        self.assertIn(self.order.id, order_ids)
        self.assertIn(self.other_order.id, order_ids)

        detail_response = self.client.get(f"/api/orders/{self.other_order.id}/")
        self.assertEqual(detail_response.status_code, drf_status.HTTP_200_OK)

    def test_client_cannot_assign_editor(self):
        self.authenticate_as_client()

        response = self.client.post(
            f"/api/orders/{self.order.id}/assign-editor/",
            {"editor_id": self.other_editor_user.id},
            format="json",
        )

        self.assertEqual(response.status_code, drf_status.HTTP_403_FORBIDDEN)

    def test_client_cannot_use_supervisor_or_settlement_actions(self):
        self.authenticate_as_client()

        protected_actions = [
            "start-review",
            "supervisor-approve",
            "supervisor-request-revision",
            "start-settlement",
            "mark-paid",
            "close",
        ]

        for action in protected_actions:
            response = self.client.post(
                f"/api/orders/{self.order.id}/{action}/",
                {},
                format="json",
            )
            self.assertIn(
                response.status_code,
                (
                    drf_status.HTTP_400_BAD_REQUEST,
                    drf_status.HTTP_403_FORBIDDEN,
                    drf_status.HTTP_404_NOT_FOUND,
                ),
                msg=f"Unexpected response for action {action}: {response.status_code}",
            )
            self.assertNotIn(
                response.status_code,
                (
                    drf_status.HTTP_200_OK,
                    drf_status.HTTP_201_CREATED,
                ),
                msg=f"Client should not be able to execute action {action}.",
            )

    def test_unassigned_editor_cannot_start_work_or_deliver(self):
        self.authenticate_as_other_editor()

        start_response = self.client.post(
            f"/api/orders/{self.order.id}/start-work/",
            {},
            format="json",
        )
        self.assert_forbidden_or_not_found(start_response)

        deliver_response = self.client.post(
            f"/api/orders/{self.order.id}/deliver/",
            {
                "file": SimpleUploadedFile(
                    "unauthorized-delivery.txt",
                    b"unauthorized delivery content",
                    content_type="text/plain",
                ),
                "note": "Unauthorized delivery attempt.",
            },
            format="multipart",
        )
        self.assert_forbidden_or_not_found(deliver_response)

    def test_comment_parent_must_belong_to_same_order(self):
        self.authenticate_as_support()

        parent_comment_on_other_order = OrderComment.objects.create(
            order=self.other_order,
            sender=self.support_user,
            target_type="order",
            text="Parent comment on other order.",
        )

        response = self.client.post(
            f"/api/orders/{self.order.id}/comments/",
            {
                "parent": parent_comment_on_other_order.id,
                "text": "Invalid cross-order reply.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, drf_status.HTTP_400_BAD_REQUEST)
        self.assertIn("parent", response.data)

    def test_comment_image_target_must_belong_to_same_order(self):
        self.authenticate_as_support()

        response = self.client.post(
            f"/api/orders/{self.order.id}/comments/",
            {
                "target_type": "image",
                "image": self.other_image.id,
                "text": "Invalid cross-order image comment.",
                "x": 10,
                "y": 20,
            },
            format="json",
        )

        self.assertEqual(response.status_code, drf_status.HTTP_400_BAD_REQUEST)

    def test_comment_delivery_target_must_belong_to_same_order(self):
        self.authenticate_as_support()

        response = self.client.post(
            f"/api/orders/{self.order.id}/comments/",
            {
                "target_type": "delivery",
                "delivery": self.other_delivery.id,
                "text": "Invalid cross-order delivery comment.",
                "x": 10,
                "y": 20,
            },
            format="json",
        )

        self.assertEqual(response.status_code, drf_status.HTTP_400_BAD_REQUEST)

    def test_resolve_comment_from_different_order_returns_404(self):
        self.authenticate_as_support()

        other_comment = OrderComment.objects.create(
            order=self.other_order,
            sender=self.support_user,
            target_type="order",
            text="Comment from other order.",
        )

        response = self.client.post(
            f"/api/orders/{self.order.id}/comments/{other_comment.id}/resolve/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, drf_status.HTTP_404_NOT_FOUND)

    def test_user_cannot_mark_other_users_notification_read(self):
        notification = OrderNotification.objects.create(
            recipient=self.client_user,
            actor=self.support_user,
            order=self.order,
            notification_type="security_test",
            title="Security notification",
            message="Security audit notification.",
            metadata={"audit": True},
        )

        self.authenticate_as_editor()

        response = self.client.post(
            f"/api/orders/notifications/{notification.id}/mark-read/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, drf_status.HTTP_404_NOT_FOUND)

    def test_user_only_lists_own_notifications(self):
        client_notification = OrderNotification.objects.create(
            recipient=self.client_user,
            actor=self.support_user,
            order=self.order,
            notification_type="client_security_test",
            title="Client notification",
            message="Client-only notification.",
            metadata={"recipient": "client"},
        )

        editor_notification = OrderNotification.objects.create(
            recipient=self.editor_user,
            actor=self.support_user,
            order=self.order,
            notification_type="editor_security_test",
            title="Editor notification",
            message="Editor-only notification.",
            metadata={"recipient": "editor"},
        )

        self.authenticate_as_client()

        response = self.client.get("/api/orders/notifications/")
        self.assertEqual(response.status_code, drf_status.HTTP_200_OK)

        items = self.get_list_items(response)
        notification_ids = {item["id"] for item in items}

        self.assertIn(client_notification.id, notification_ids)
        self.assertNotIn(editor_notification.id, notification_ids)