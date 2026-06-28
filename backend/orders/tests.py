import shutil
import tempfile
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from accounts.models import EditorProfile
from orders.models import Order, OrderDelivery, OrderRating


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
class OrderCommentsAndNotificationsAPITests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        User = get_user_model()

        self.client_user = User.objects.create_user(
            username="client_test",
            password="ClientPass123!",
            role="client",
        )
        self.editor_user = User.objects.create_user(
            username="editor_test",
            password="EditorPass123!",
            role="editor",
        )
        self.support_user = User.objects.create_user(
            username="support_test",
            password="SupportPass123!",
            role="support",
            is_staff=True,
        )

        self.order = Order.objects.create(
            client=self.client_user,
            editor=self.editor_user,
            title="Automated test order",
            description="Order used for API workflow tests.",
            deadline=timezone.now() + timedelta(days=5),
        )

        self.image = OrderImage.objects.create(
            order=self.order,
            image=SimpleUploadedFile(
                "original-test.jpg",
                b"fake image content",
                content_type="image/jpeg",
            ),
            note="Original test image",
        )

        self.delivery = OrderDelivery.objects.create(
            order=self.order,
            file=SimpleUploadedFile(
                "delivery-test.txt",
                b"fake delivery content",
                content_type="text/plain",
            ),
            note="Delivery test file",
            uploaded_by=self.editor_user,
        )

    def authenticate_as_support(self):
        self.client.force_authenticate(user=self.support_user)

    def authenticate_as_client(self):
        self.client.force_authenticate(user=self.client_user)

    def authenticate_as_editor(self):
        self.client.force_authenticate(user=self.editor_user)

    def test_create_threaded_comment_and_reply(self):
        self.authenticate_as_support()

        root_url = f"/api/orders/{self.order.id}/comments/"
        root_response = self.client.post(
            root_url,
            {
                "target_type": "order",
                "text": "Root comment from automated test.",
            },
            format="json",
        )

        self.assertEqual(root_response.status_code, drf_status.HTTP_201_CREATED)
        root_comment_id = root_response.data["id"]
        self.assertIsNone(root_response.data["parent"])

        reply_response = self.client.post(
            root_url,
            {
                "parent": root_comment_id,
                "text": "Reply from automated test.",
            },
            format="json",
        )

        self.assertEqual(reply_response.status_code, drf_status.HTTP_201_CREATED)
        self.assertEqual(reply_response.data["parent"], root_comment_id)
        self.assertEqual(reply_response.data["target_type"], "order")

        threads_response = self.client.get(
            f"/api/orders/{self.order.id}/comment-threads/"
        )

        self.assertEqual(threads_response.status_code, drf_status.HTTP_200_OK)

        root_thread = None
        for item in threads_response.data:
            if item["id"] == root_comment_id:
                root_thread = item
                break

        self.assertIsNotNone(root_thread)
        self.assertEqual(len(root_thread["replies"]), 1)
        self.assertEqual(root_thread["replies"][0]["parent"], root_comment_id)

    def test_resolve_unresolve_comment_and_filter(self):
        self.authenticate_as_support()

        comment = OrderComment.objects.create(
            order=self.order,
            sender=self.support_user,
            target_type="order",
            text="Comment to resolve.",
        )

        resolve_response = self.client.post(
            f"/api/orders/{self.order.id}/comments/{comment.id}/resolve/"
        )

        self.assertEqual(resolve_response.status_code, drf_status.HTTP_200_OK)
        self.assertTrue(resolve_response.data["is_resolved"])
        self.assertEqual(resolve_response.data["resolved_by"], self.support_user.id)

        resolved_list_response = self.client.get(
            f"/api/orders/{self.order.id}/comments/?resolved=true"
        )

        self.assertEqual(resolved_list_response.status_code, drf_status.HTTP_200_OK)
        resolved_ids = [item["id"] for item in resolved_list_response.data]
        self.assertIn(comment.id, resolved_ids)

        unresolved_list_response = self.client.get(
            f"/api/orders/{self.order.id}/comments/?resolved=false"
        )

        self.assertEqual(unresolved_list_response.status_code, drf_status.HTTP_200_OK)
        unresolved_ids = [item["id"] for item in unresolved_list_response.data]
        self.assertNotIn(comment.id, unresolved_ids)

        unresolve_response = self.client.post(
            f"/api/orders/{self.order.id}/comments/{comment.id}/unresolve/"
        )

        self.assertEqual(unresolve_response.status_code, drf_status.HTTP_200_OK)
        self.assertFalse(unresolve_response.data["is_resolved"])
        self.assertIsNone(unresolve_response.data["resolved_by"])
        self.assertIsNone(unresolve_response.data["resolved_at"])

    def test_create_point_annotation_and_filter(self):
        self.authenticate_as_support()

        response = self.client.post(
            f"/api/orders/{self.order.id}/comments/",
            {
                "target_type": "delivery",
                "delivery": self.delivery.id,
                "text": "Point annotation test.",
                "x": 42.5,
                "y": 58.3,
                "annotation_type": "point",
                "annotation_label": "Skin smoothing",
                "annotation_color": "#ff0000",
                "annotation_data": {
                    "priority": "high",
                    "tool": "pin",
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, drf_status.HTTP_201_CREATED)
        self.assertEqual(response.data["annotation_type"], "point")
        self.assertEqual(response.data["annotation_label"], "Skin smoothing")
        self.assertEqual(response.data["annotation_color"], "#ff0000")

        filter_response = self.client.get(
            f"/api/orders/{self.order.id}/comments/?has_annotation=true"
        )

        self.assertEqual(filter_response.status_code, drf_status.HTTP_200_OK)
        self.assertGreaterEqual(len(filter_response.data), 1)

        annotation_types = [item["annotation_type"] for item in filter_response.data]
        self.assertIn("point", annotation_types)

        point_filter_response = self.client.get(
            f"/api/orders/{self.order.id}/comments/?annotation_type=point"
        )

        self.assertEqual(point_filter_response.status_code, drf_status.HTTP_200_OK)
        self.assertTrue(
            all(
                item["annotation_type"] == "point"
                for item in point_filter_response.data
            )
        )

    def test_point_annotation_requires_coordinates(self):
        self.authenticate_as_support()

        response = self.client.post(
            f"/api/orders/{self.order.id}/comments/",
            {
                "target_type": "delivery",
                "delivery": self.delivery.id,
                "text": "Invalid point annotation.",
                "annotation_type": "point",
                "annotation_label": "Invalid point",
            },
            format="json",
        )

        self.assertEqual(response.status_code, drf_status.HTTP_400_BAD_REQUEST)
        self.assertIn("annotation_type", response.data)

    def test_order_level_rich_annotation_is_not_allowed(self):
        self.authenticate_as_support()

        response = self.client.post(
            f"/api/orders/{self.order.id}/comments/",
            {
                "target_type": "order",
                "text": "Invalid order-level annotation.",
                "annotation_type": "rectangle",
                "annotation_label": "Invalid",
                "annotation_data": {
                    "width": 20,
                    "height": 20,
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, drf_status.HTTP_400_BAD_REQUEST)
        self.assertIn("annotation_type", response.data)

    def test_comment_creation_creates_notifications_for_client_and_editor(self):
        self.authenticate_as_support()

        response = self.client.post(
            f"/api/orders/{self.order.id}/comments/",
            {
                "target_type": "order",
                "text": "Notification test comment.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, drf_status.HTTP_201_CREATED)

        notifications = OrderNotification.objects.filter(
            order=self.order,
            notification_type="comment_created",
        )

        self.assertEqual(notifications.count(), 2)

        recipient_ids = set(notifications.values_list("recipient_id", flat=True))
        self.assertIn(self.client_user.id, recipient_ids)
        self.assertIn(self.editor_user.id, recipient_ids)
        self.assertNotIn(self.support_user.id, recipient_ids)

    def test_client_can_list_and_mark_own_notification_read(self):
        self.authenticate_as_support()

        self.client.post(
            f"/api/orders/{self.order.id}/comments/",
            {
                "target_type": "order",
                "text": "Notification read test.",
            },
            format="json",
        )

        self.authenticate_as_client()

        list_response = self.client.get("/api/orders/notifications/")
        self.assertEqual(list_response.status_code, drf_status.HTTP_200_OK)

        if isinstance(list_response.data, dict) and "results" in list_response.data:
            notifications = list_response.data["results"]
        else:
            notifications = list_response.data

        self.assertGreaterEqual(len(notifications), 1)

        notification_id = notifications[0]["id"]

        unread_count_response = self.client.get(
            "/api/orders/notifications/unread-count/"
        )
        self.assertEqual(unread_count_response.status_code, drf_status.HTTP_200_OK)
        self.assertGreaterEqual(unread_count_response.data["unread_count"], 1)

        mark_read_response = self.client.post(
            f"/api/orders/notifications/{notification_id}/mark-read/"
        )

        self.assertEqual(mark_read_response.status_code, drf_status.HTTP_200_OK)
        self.assertTrue(mark_read_response.data["is_read"])

    def test_user_cannot_mark_other_users_notification_read(self):
        self.authenticate_as_support()

        self.client.post(
            f"/api/orders/{self.order.id}/comments/",
            {
                "target_type": "order",
                "text": "Notification security test.",
            },
            format="json",
        )

        client_notification = OrderNotification.objects.filter(
            recipient=self.client_user
        ).first()

        self.assertIsNotNone(client_notification)

        self.authenticate_as_editor()

        response = self.client.post(
            f"/api/orders/notifications/{client_notification.id}/mark-read/"
        )

        self.assertEqual(response.status_code, drf_status.HTTP_404_NOT_FOUND)


class OrderRatingAndPublicationModelTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.client_user = User.objects.create_user(
            username="rating-client",
            password="pass12345",
            role="client",
        )
        self.other_client = User.objects.create_user(
            username="rating-other-client",
            password="pass12345",
            role="client",
        )
        self.editor_user = User.objects.create_user(
            username="rating-editor",
            password="pass12345",
            role="editor",
        )
        self.supervisor_user = User.objects.create_user(
            username="rating-supervisor",
            password="pass12345",
            role="supervisor",
        )

        self.editor_profile = EditorProfile.objects.create(
            user=self.editor_user,
            display_name="Rating Editor",
            base_price=1000,
            average_delivery_hours=24,
        )

        self.order = Order.objects.create(
            client=self.client_user,
            editor=self.editor_user,
            title="Rating Order",
            description="Rating order description",
            status=Order.Status.COMPLETED,
        )
        self.second_order = Order.objects.create(
            client=self.other_client,
            editor=self.editor_user,
            title="Second Rating Order",
            description="Second rating order description",
            status=Order.Status.COMPLETED,
        )

    def test_client_rating_updates_editor_rating_average(self):
        OrderRating.objects.create(
            order=self.order,
            rated_by=self.client_user,
            source=OrderRating.Source.CLIENT,
            score=8,
            comment="Great work",
        )

        self.editor_profile.refresh_from_db()

        self.assertEqual(float(self.editor_profile.rating_average), 8.0)

    def test_editor_rating_average_uses_only_client_ratings(self):
        OrderRating.objects.create(
            order=self.order,
            rated_by=self.supervisor_user,
            source=OrderRating.Source.SUPERVISOR,
            score=10,
            comment="Internal quality score",
        )

        self.editor_profile.refresh_from_db()

        self.assertEqual(float(self.editor_profile.rating_average), 0.0)

        OrderRating.objects.create(
            order=self.order,
            rated_by=self.client_user,
            source=OrderRating.Source.CLIENT,
            score=8,
            comment="Client score",
        )
        OrderRating.objects.create(
            order=self.second_order,
            rated_by=self.other_client,
            source=OrderRating.Source.CLIENT,
            score=6,
            comment="Second client score",
        )

        self.editor_profile.refresh_from_db()

        self.assertEqual(float(self.editor_profile.rating_average), 7.0)

    def test_updating_client_rating_recalculates_editor_rating_average(self):
        rating = OrderRating.objects.create(
            order=self.order,
            rated_by=self.client_user,
            source=OrderRating.Source.CLIENT,
            score=8,
            comment="Initial score",
        )

        rating.score = 10
        rating.save()

        self.editor_profile.refresh_from_db()

        self.assertEqual(float(self.editor_profile.rating_average), 10.0)

    def test_deleting_client_rating_recalculates_editor_rating_average(self):
        rating = OrderRating.objects.create(
            order=self.order,
            rated_by=self.client_user,
            source=OrderRating.Source.CLIENT,
            score=8,
            comment="Client score",
        )

        rating.delete()

        self.editor_profile.refresh_from_db()

        self.assertEqual(float(self.editor_profile.rating_average), 0.0)

    def test_order_delivery_publication_request_and_approval_flow(self):
        delivery = OrderDelivery.objects.create(
            order=self.order,
            uploaded_by=self.editor_user,
            file=SimpleUploadedFile(
                "delivery.jpg",
                b"fake-image-content",
                content_type="image/jpeg",
            ),
            note="Final delivery",
        )

        self.assertEqual(
            delivery.publication_status,
            OrderDelivery.PublicationStatus.PRIVATE,
        )
        self.assertFalse(delivery.is_public)

        delivery.request_publication(self.editor_user)
        delivery.refresh_from_db()

        self.assertEqual(
            delivery.publication_status,
            OrderDelivery.PublicationStatus.REQUESTED,
        )
        self.assertEqual(delivery.publication_requested_by, self.editor_user)
        self.assertIsNotNone(delivery.publication_requested_at)
        self.assertFalse(delivery.is_public)

        delivery.approve_publication(
            reviewed_by=self.client_user,
            note="Approved by owner",
        )
        delivery.refresh_from_db()

        self.assertEqual(
            delivery.publication_status,
            OrderDelivery.PublicationStatus.APPROVED,
        )
        self.assertEqual(delivery.publication_reviewed_by, self.client_user)
        self.assertIsNotNone(delivery.publication_reviewed_at)
        self.assertEqual(delivery.publication_note, "Approved by owner")
        self.assertTrue(delivery.is_public)

    def test_order_delivery_publication_rejection_flow(self):
        delivery = OrderDelivery.objects.create(
            order=self.order,
            uploaded_by=self.editor_user,
            file=SimpleUploadedFile(
                "delivery-rejected.jpg",
                b"fake-image-content",
                content_type="image/jpeg",
            ),
            note="Final delivery",
        )

        delivery.request_publication(self.editor_user)
        delivery.reject_publication(
            reviewed_by=self.client_user,
            note="Do not publish this work",
        )
        delivery.refresh_from_db()

        self.assertEqual(
            delivery.publication_status,
            OrderDelivery.PublicationStatus.REJECTED,
        )
        self.assertEqual(delivery.publication_reviewed_by, self.client_user)
        self.assertIsNotNone(delivery.publication_reviewed_at)
        self.assertEqual(delivery.publication_note, "Do not publish this work")
        self.assertFalse(delivery.is_public)


class OrderDeliveryPublicationAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()

        self.client_user = User.objects.create_user(
            username="publication-client",
            password="pass12345",
            role="client",
        )
        self.editor_user = User.objects.create_user(
            username="publication-editor",
            password="pass12345",
            role="editor",
        )
        self.other_user = User.objects.create_user(
            username="publication-other",
            password="pass12345",
            role="client",
        )
        self.supervisor_user = User.objects.create_user(
            username="publication-supervisor",
            password="pass12345",
            role="supervisor",
        )

        self.order = Order.objects.create(
            client=self.client_user,
            editor=self.editor_user,
            title="Publication API Order",
            description="Publication API order description",
            status=Order.Status.DELIVERED,
        )

        self.delivery = OrderDelivery.objects.create(
            order=self.order,
            uploaded_by=self.editor_user,
            file=SimpleUploadedFile(
                "publication-delivery.jpg",
                b"fake-delivery-content",
                content_type="image/jpeg",
            ),
            note="Final delivery",
        )

    def _request_publication_url(self):
        return reverse(
            "orders-request-delivery-publication",
            kwargs={
                "pk": self.order.pk,
                "delivery_id": self.delivery.pk,
            },
        )

    def _approve_publication_url(self):
        return reverse(
            "orders-approve-delivery-publication",
            kwargs={
                "pk": self.order.pk,
                "delivery_id": self.delivery.pk,
            },
        )

    def _reject_publication_url(self):
        return reverse(
            "orders-reject-delivery-publication",
            kwargs={
                "pk": self.order.pk,
                "delivery_id": self.delivery.pk,
            },
        )

    def test_assigned_editor_can_request_delivery_publication(self):
        self.client.force_authenticate(self.editor_user)

        response = self.client.post(self._request_publication_url())

        self.assertEqual(response.status_code, 200)

        self.delivery.refresh_from_db()
        self.assertEqual(
            self.delivery.publication_status,
            OrderDelivery.PublicationStatus.REQUESTED,
        )
        self.assertEqual(
            self.delivery.publication_requested_by,
            self.editor_user,
        )
        self.assertIsNotNone(self.delivery.publication_requested_at)
        self.assertFalse(self.delivery.is_public)

    def test_non_assigned_user_cannot_request_delivery_publication(self):
        self.client.force_authenticate(self.other_user)

        response = self.client.post(self._request_publication_url())

        self.assertEqual(response.status_code, 404)

        self.delivery.refresh_from_db()
        self.assertEqual(
            self.delivery.publication_status,
            OrderDelivery.PublicationStatus.PRIVATE,
        )

    def test_order_owner_can_approve_requested_delivery_publication(self):
        self.delivery.request_publication(self.editor_user)

        self.client.force_authenticate(self.client_user)

        response = self.client.post(
            self._approve_publication_url(),
            {"note": "Approved by owner"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.delivery.refresh_from_db()
        self.assertEqual(
            self.delivery.publication_status,
            OrderDelivery.PublicationStatus.APPROVED,
        )
        self.assertEqual(
            self.delivery.publication_reviewed_by,
            self.client_user,
        )
        self.assertEqual(self.delivery.publication_note, "Approved by owner")
        self.assertTrue(self.delivery.is_public)

    def test_other_user_cannot_approve_delivery_publication(self):
        self.delivery.request_publication(self.editor_user)

        self.client.force_authenticate(self.other_user)

        response = self.client.post(
            self._approve_publication_url(),
            {"note": "Trying to approve"},
            format="json",
        )

        self.assertEqual(response.status_code, 404)

        self.delivery.refresh_from_db()
        self.assertEqual(
            self.delivery.publication_status,
            OrderDelivery.PublicationStatus.REQUESTED,
        )
        self.assertFalse(self.delivery.is_public)

    def test_order_owner_can_reject_requested_delivery_publication(self):
        self.delivery.request_publication(self.editor_user)

        self.client.force_authenticate(self.client_user)

        response = self.client.post(
            self._reject_publication_url(),
            {"note": "Do not publish"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.delivery.refresh_from_db()
        self.assertEqual(
            self.delivery.publication_status,
            OrderDelivery.PublicationStatus.REJECTED,
        )
        self.assertEqual(
            self.delivery.publication_reviewed_by,
            self.client_user,
        )
        self.assertEqual(self.delivery.publication_note, "Do not publish")
        self.assertFalse(self.delivery.is_public)

    def test_supervisor_can_manage_delivery_publication(self):
        self.client.force_authenticate(self.supervisor_user)

        request_response = self.client.post(self._request_publication_url())

        self.assertEqual(request_response.status_code, 200)

        approve_response = self.client.post(
            self._approve_publication_url(),
            {"note": "Approved by supervisor"},
            format="json",
        )

        self.assertEqual(approve_response.status_code, 200)

        self.delivery.refresh_from_db()
        self.assertEqual(
            self.delivery.publication_status,
            OrderDelivery.PublicationStatus.APPROVED,
        )
        self.assertEqual(
            self.delivery.publication_reviewed_by,
            self.supervisor_user,
        )
        self.assertTrue(self.delivery.is_public)

    def test_cannot_approve_delivery_without_publication_request(self):
        self.client.force_authenticate(self.client_user)

        response = self.client.post(
            self._approve_publication_url(),
            {"note": "Approve without request"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        self.delivery.refresh_from_db()
        self.assertEqual(
            self.delivery.publication_status,
            OrderDelivery.PublicationStatus.PRIVATE,
        )
        self.assertFalse(self.delivery.is_public)


class OrderCommentPublicVisibilityTests(APITestCase):
    def setUp(self):
        User = get_user_model()

        self.client_user = User.objects.create_user(
            username="comment-public-client",
            password="pass12345",
            role="client",
        )
        self.editor_user = User.objects.create_user(
            username="comment-public-editor",
            password="pass12345",
            role="editor",
        )

        self.order = Order.objects.create(
            client=self.client_user,
            editor=self.editor_user,
            title="Comment Public Visibility Order",
            description="Testing public comment visibility",
            status=Order.Status.DELIVERED,
        )

        self.public_delivery = OrderDelivery.objects.create(
            order=self.order,
            uploaded_by=self.editor_user,
            file=SimpleUploadedFile(
                "public-delivery.jpg",
                b"public-delivery-content",
                content_type="image/jpeg",
            ),
            publication_status=OrderDelivery.PublicationStatus.APPROVED,
        )

        self.private_delivery = OrderDelivery.objects.create(
            order=self.order,
            uploaded_by=self.editor_user,
            file=SimpleUploadedFile(
                "private-delivery.jpg",
                b"private-delivery-content",
                content_type="image/jpeg",
            ),
            publication_status=OrderDelivery.PublicationStatus.PRIVATE,
        )

    def _comments_url(self):
        return reverse(
            "orders-comments",
            kwargs={"pk": self.order.pk},
        )

    def test_approved_comment_on_approved_delivery_is_publicly_visible(self):
        comment = OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.public_delivery,
            text="Public approved delivery comment",
            status=OrderComment.Status.APPROVED,
        )

        self.assertTrue(comment.is_publicly_visible)

    def test_approved_comment_on_private_delivery_is_not_publicly_visible(self):
        comment = OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.private_delivery,
            text="Approved but private delivery comment",
            status=OrderComment.Status.APPROVED,
        )

        self.assertFalse(comment.is_publicly_visible)

    def test_active_comment_on_approved_delivery_is_not_publicly_visible(self):
        comment = OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.public_delivery,
            text="Active private comment",
            status=OrderComment.Status.ACTIVE,
        )

        self.assertFalse(comment.is_publicly_visible)

    def test_order_level_approved_comment_is_not_publicly_visible(self):
        comment = OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.ORDER,
            text="Approved order-level comment",
            status=OrderComment.Status.APPROVED,
        )

        self.assertFalse(comment.is_publicly_visible)

    def test_public_comment_filter_returns_only_publicly_visible_comments(self):
        public_comment = OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.public_delivery,
            text="Visible public comment",
            status=OrderComment.Status.APPROVED,
        )

        private_delivery_comment = OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.private_delivery,
            text="Approved but delivery is private",
            status=OrderComment.Status.APPROVED,
        )

        active_comment = OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.public_delivery,
            text="Delivery public but comment active",
            status=OrderComment.Status.ACTIVE,
        )

        self.client.force_authenticate(self.client_user)

        response = self.client.get(
            self._comments_url(),
            {"public": "true"},
        )

        self.assertEqual(response.status_code, 200)

        returned_ids = {item["id"] for item in response.data}

        self.assertIn(public_comment.id, returned_ids)
        self.assertNotIn(private_delivery_comment.id, returned_ids)
        self.assertNotIn(active_comment.id, returned_ids)
        self.assertEqual(len(returned_ids), 1)

        returned_comment = response.data[0]
        self.assertTrue(returned_comment["is_publicly_visible"])

    def test_private_comment_filter_excludes_publicly_visible_comments(self):
        public_comment = OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.public_delivery,
            text="Visible public comment",
            status=OrderComment.Status.APPROVED,
        )

        private_comment = OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.public_delivery,
            text="Private active comment",
            status=OrderComment.Status.ACTIVE,
        )

        private_delivery_comment = OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.private_delivery,
            text="Approved but delivery private",
            status=OrderComment.Status.APPROVED,
        )

        self.client.force_authenticate(self.client_user)

        response = self.client.get(
            self._comments_url(),
            {"public": "false"},
        )

        self.assertEqual(response.status_code, 200)

        returned_ids = {item["id"] for item in response.data}

        self.assertNotIn(public_comment.id, returned_ids)
        self.assertIn(private_comment.id, returned_ids)
        self.assertIn(private_delivery_comment.id, returned_ids)

    def test_deleted_public_comment_is_not_returned_in_public_filter(self):
        deleted_comment = OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.public_delivery,
            text="Deleted public comment",
            status=OrderComment.Status.DELETED,
        )

        self.client.force_authenticate(self.client_user)

        response = self.client.get(
            self._comments_url(),
            {"public": "true"},
        )

        self.assertEqual(response.status_code, 200)

        returned_ids = {item["id"] for item in response.data}

        self.assertNotIn(deleted_comment.id, returned_ids)
        self.assertEqual(len(returned_ids), 0)


class PublicOrderDeliveryAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()

        self.client_user = User.objects.create_user(
            username="public-delivery-client",
            password="pass12345",
            role="client",
        )
        self.editor_user = User.objects.create_user(
            username="public-delivery-editor",
            password="pass12345",
            role="editor",
        )

        self.order = Order.objects.create(
            client=self.client_user,
            editor=self.editor_user,
            title="Public Delivery Order",
            description="Testing public delivery endpoint",
            status=Order.Status.DELIVERED,
        )

        self.public_delivery = OrderDelivery.objects.create(
            order=self.order,
            uploaded_by=self.editor_user,
            file=SimpleUploadedFile(
                "approved-public-delivery.jpg",
                b"approved-public-delivery-content",
                content_type="image/jpeg",
            ),
            note="Approved public delivery",
            publication_status=OrderDelivery.PublicationStatus.APPROVED,
        )

        self.private_delivery = OrderDelivery.objects.create(
            order=self.order,
            uploaded_by=self.editor_user,
            file=SimpleUploadedFile(
                "private-delivery.jpg",
                b"private-delivery-content",
                content_type="image/jpeg",
            ),
            note="Private delivery",
            publication_status=OrderDelivery.PublicationStatus.PRIVATE,
        )

        self.requested_delivery = OrderDelivery.objects.create(
            order=self.order,
            uploaded_by=self.editor_user,
            file=SimpleUploadedFile(
                "requested-delivery.jpg",
                b"requested-delivery-content",
                content_type="image/jpeg",
            ),
            note="Requested delivery",
            publication_status=OrderDelivery.PublicationStatus.REQUESTED,
        )

        self.rejected_delivery = OrderDelivery.objects.create(
            order=self.order,
            uploaded_by=self.editor_user,
            file=SimpleUploadedFile(
                "rejected-delivery.jpg",
                b"rejected-delivery-content",
                content_type="image/jpeg",
            ),
            note="Rejected delivery",
            publication_status=OrderDelivery.PublicationStatus.REJECTED,
        )

    def _public_deliveries_url(self):
        return reverse("orders-public-deliveries")

    def test_anonymous_user_can_list_public_deliveries(self):
        response = self.client.get(self._public_deliveries_url())

        self.assertEqual(response.status_code, 200)

    def test_public_deliveries_endpoint_returns_only_approved_deliveries(self):
        response = self.client.get(self._public_deliveries_url())

        self.assertEqual(response.status_code, 200)

        returned_ids = {item["id"] for item in response.data}

        self.assertIn(self.public_delivery.id, returned_ids)
        self.assertNotIn(self.private_delivery.id, returned_ids)
        self.assertNotIn(self.requested_delivery.id, returned_ids)
        self.assertNotIn(self.rejected_delivery.id, returned_ids)
        self.assertEqual(len(returned_ids), 1)

    def test_public_delivery_response_contains_public_fields(self):
        response = self.client.get(self._public_deliveries_url())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        item = response.data[0]

        self.assertEqual(item["id"], self.public_delivery.id)
        self.assertEqual(item["order"], self.order.id)
        self.assertEqual(item["order_title"], self.order.title)
        self.assertEqual(item["uploaded_by"], self.editor_user.id)
        self.assertEqual(item["uploaded_by_username"], self.editor_user.username)
        self.assertEqual(
            item["publication_status"],
            OrderDelivery.PublicationStatus.APPROVED,
        )
        self.assertTrue(item["is_public"])


class PublicOrderDeliveryDetailAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()

        self.client_user = User.objects.create_user(
            username="public-delivery-detail-client",
            password="pass12345",
            role="client",
        )
        self.editor_user = User.objects.create_user(
            username="public-delivery-detail-editor",
            password="pass12345",
            role="editor",
        )

        self.order = Order.objects.create(
            client=self.client_user,
            editor=self.editor_user,
            title="Public Delivery Detail Order",
            description="Testing public delivery detail endpoint",
            status=Order.Status.DELIVERED,
        )

        self.public_delivery = OrderDelivery.objects.create(
            order=self.order,
            uploaded_by=self.editor_user,
            file=SimpleUploadedFile(
                "public-detail-delivery.jpg",
                b"public-detail-delivery-content",
                content_type="image/jpeg",
            ),
            note="Approved public delivery detail",
            publication_status=OrderDelivery.PublicationStatus.APPROVED,
        )

        self.private_delivery = OrderDelivery.objects.create(
            order=self.order,
            uploaded_by=self.editor_user,
            file=SimpleUploadedFile(
                "private-detail-delivery.jpg",
                b"private-detail-delivery-content",
                content_type="image/jpeg",
            ),
            note="Private delivery detail",
            publication_status=OrderDelivery.PublicationStatus.PRIVATE,
        )

    def _public_delivery_detail_url(self, delivery):
        return reverse(
            "orders-public-delivery-detail",
            kwargs={"delivery_id": delivery.id},
        )

    def test_anonymous_user_can_retrieve_public_delivery_detail(self):
        response = self.client.get(
            self._public_delivery_detail_url(self.public_delivery)
        )

        self.assertEqual(response.status_code, 200)

    def test_private_delivery_detail_returns_404(self):
        response = self.client.get(
            self._public_delivery_detail_url(self.private_delivery)
        )

        self.assertEqual(response.status_code, 404)

    def test_public_delivery_detail_contains_public_comments_only(self):
        public_comment = OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.public_delivery,
            text="Approved public comment",
            status=OrderComment.Status.APPROVED,
        )

        active_comment = OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.public_delivery,
            text="Active private comment",
            status=OrderComment.Status.ACTIVE,
        )

        deleted_comment = OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.public_delivery,
            text="Deleted comment",
            status=OrderComment.Status.DELETED,
        )

        order_level_comment = OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.ORDER,
            text="Order level approved comment",
            status=OrderComment.Status.APPROVED,
        )

        response = self.client.get(
            self._public_delivery_detail_url(self.public_delivery)
        )

        self.assertEqual(response.status_code, 200)

        returned_ids = {item["id"] for item in response.data["public_comments"]}

        self.assertIn(public_comment.id, returned_ids)
        self.assertNotIn(active_comment.id, returned_ids)
        self.assertNotIn(deleted_comment.id, returned_ids)
        self.assertNotIn(order_level_comment.id, returned_ids)
        self.assertEqual(len(returned_ids), 1)

    def test_public_delivery_detail_response_contains_delivery_fields(self):
        response = self.client.get(
            self._public_delivery_detail_url(self.public_delivery)
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data["id"], self.public_delivery.id)
        self.assertEqual(response.data["order"], self.order.id)
        self.assertEqual(response.data["order_title"], self.order.title)
        self.assertEqual(response.data["uploaded_by"], self.editor_user.id)
        self.assertEqual(
            response.data["uploaded_by_username"],
            self.editor_user.username,
        )
        self.assertEqual(
            response.data["publication_status"],
            OrderDelivery.PublicationStatus.APPROVED,
        )
        self.assertTrue(response.data["is_public"])
        self.assertIn("public_comments", response.data)


class PublicOrderDeliveryFilterAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()

        self.client_user = User.objects.create_user(
            username="public-filter-client",
            password="pass12345",
            role="client",
        )
        self.editor_one = User.objects.create_user(
            username="filter-editor-one",
            password="pass12345",
            role="editor",
        )
        self.editor_two = User.objects.create_user(
            username="filter-editor-two",
            password="pass12345",
            role="editor",
        )

        self.order_one = Order.objects.create(
            client=self.client_user,
            editor=self.editor_one,
            title="Beauty Portrait Retouch",
            description="Testing public delivery filters",
            status=Order.Status.DELIVERED,
        )

        self.order_two = Order.objects.create(
            client=self.client_user,
            editor=self.editor_two,
            title="Product Photo Cleanup",
            description="Testing second public delivery filter",
            status=Order.Status.DELIVERED,
        )

        self.delivery_one = OrderDelivery.objects.create(
            order=self.order_one,
            uploaded_by=self.editor_one,
            file=SimpleUploadedFile(
                "beauty-retouch.jpg",
                b"beauty-retouch-content",
                content_type="image/jpeg",
            ),
            note="Soft skin retouch sample",
            publication_status=OrderDelivery.PublicationStatus.APPROVED,
        )

        self.delivery_two = OrderDelivery.objects.create(
            order=self.order_two,
            uploaded_by=self.editor_two,
            file=SimpleUploadedFile(
                "product-cleanup.jpg",
                b"product-cleanup-content",
                content_type="image/jpeg",
            ),
            note="White background product cleanup",
            publication_status=OrderDelivery.PublicationStatus.APPROVED,
        )

        self.private_delivery = OrderDelivery.objects.create(
            order=self.order_one,
            uploaded_by=self.editor_two,
            file=SimpleUploadedFile(
                "private-filter.jpg",
                b"private-filter-content",
                content_type="image/jpeg",
            ),
            note="Private hidden delivery",
            publication_status=OrderDelivery.PublicationStatus.PRIVATE,
        )

    def _public_deliveries_url(self):
        return reverse("orders-public-deliveries")

    def test_filter_public_deliveries_by_editor_id(self):
        response = self.client.get(
            self._public_deliveries_url(),
            {"editor": self.editor_one.id},
        )

        self.assertEqual(response.status_code, 200)

        returned_ids = {item["id"] for item in response.data}

        self.assertIn(self.delivery_one.id, returned_ids)
        self.assertNotIn(self.delivery_two.id, returned_ids)
        self.assertNotIn(self.private_delivery.id, returned_ids)
        self.assertEqual(len(returned_ids), 1)

    def test_filter_public_deliveries_by_editor_username(self):
        response = self.client.get(
            self._public_deliveries_url(),
            {"editor_username": "editor-two"},
        )

        self.assertEqual(response.status_code, 200)

        returned_ids = {item["id"] for item in response.data}

        self.assertIn(self.delivery_two.id, returned_ids)
        self.assertNotIn(self.delivery_one.id, returned_ids)
        self.assertNotIn(self.private_delivery.id, returned_ids)
        self.assertEqual(len(returned_ids), 1)

    def test_filter_public_deliveries_by_order_id(self):
        response = self.client.get(
            self._public_deliveries_url(),
            {"order": self.order_one.id},
        )

        self.assertEqual(response.status_code, 200)

        returned_ids = {item["id"] for item in response.data}

        self.assertIn(self.delivery_one.id, returned_ids)
        self.assertNotIn(self.delivery_two.id, returned_ids)
        self.assertNotIn(self.private_delivery.id, returned_ids)
        self.assertEqual(len(returned_ids), 1)

    def test_search_public_deliveries_by_order_title(self):
        response = self.client.get(
            self._public_deliveries_url(),
            {"search": "beauty"},
        )

        self.assertEqual(response.status_code, 200)

        returned_ids = {item["id"] for item in response.data}

        self.assertIn(self.delivery_one.id, returned_ids)
        self.assertNotIn(self.delivery_two.id, returned_ids)
        self.assertNotIn(self.private_delivery.id, returned_ids)
        self.assertEqual(len(returned_ids), 1)

    def test_search_public_deliveries_by_note(self):
        response = self.client.get(
            self._public_deliveries_url(),
            {"search": "product cleanup"},
        )

        self.assertEqual(response.status_code, 200)

        returned_ids = {item["id"] for item in response.data}

        self.assertIn(self.delivery_two.id, returned_ids)
        self.assertNotIn(self.delivery_one.id, returned_ids)
        self.assertNotIn(self.private_delivery.id, returned_ids)
        self.assertEqual(len(returned_ids), 1)

    def test_search_public_deliveries_by_editor_username(self):
        response = self.client.get(
            self._public_deliveries_url(),
            {"search": "filter-editor-one"},
        )

        self.assertEqual(response.status_code, 200)

        returned_ids = {item["id"] for item in response.data}

        self.assertIn(self.delivery_one.id, returned_ids)
        self.assertNotIn(self.delivery_two.id, returned_ids)
        self.assertNotIn(self.private_delivery.id, returned_ids)
        self.assertEqual(len(returned_ids), 1)


class PublicOrderDeliveryCommentCountTests(APITestCase):
    def setUp(self):
        User = get_user_model()

        self.client_user = User.objects.create_user(
            username="public-count-client",
            password="pass12345",
            role="client",
        )
        self.editor_user = User.objects.create_user(
            username="public-count-editor",
            password="pass12345",
            role="editor",
        )

        self.order = Order.objects.create(
            client=self.client_user,
            editor=self.editor_user,
            title="Public Comment Count Order",
            description="Testing public comment counts",
            status=Order.Status.DELIVERED,
        )

        self.public_delivery = OrderDelivery.objects.create(
            order=self.order,
            uploaded_by=self.editor_user,
            file=SimpleUploadedFile(
                "public-count-delivery.jpg",
                b"public-count-delivery-content",
                content_type="image/jpeg",
            ),
            note="Delivery with public comments",
            publication_status=OrderDelivery.PublicationStatus.APPROVED,
        )

        self.other_public_delivery = OrderDelivery.objects.create(
            order=self.order,
            uploaded_by=self.editor_user,
            file=SimpleUploadedFile(
                "other-public-count-delivery.jpg",
                b"other-public-count-delivery-content",
                content_type="image/jpeg",
            ),
            note="Another public delivery",
            publication_status=OrderDelivery.PublicationStatus.APPROVED,
        )

    def _public_deliveries_url(self):
        return reverse("orders-public-deliveries")

    def _public_delivery_detail_url(self, delivery):
        return reverse(
            "orders-public-delivery-detail",
            kwargs={"delivery_id": delivery.id},
        )

    def test_public_delivery_list_contains_public_comments_count(self):
        OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.public_delivery,
            text="Approved public comment 1",
            status=OrderComment.Status.APPROVED,
        )

        OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.public_delivery,
            text="Approved public comment 2",
            status=OrderComment.Status.APPROVED,
        )

        OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.public_delivery,
            text="Active private comment",
            status=OrderComment.Status.ACTIVE,
        )

        response = self.client.get(self._public_deliveries_url())

        self.assertEqual(response.status_code, 200)

        item = next(
            item for item in response.data if item["id"] == self.public_delivery.id
        )

        self.assertEqual(item["public_comments_count"], 2)

    def test_public_delivery_detail_contains_public_comments_count(self):
        OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.public_delivery,
            text="Approved public comment",
            status=OrderComment.Status.APPROVED,
        )

        OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.public_delivery,
            text="Deleted comment",
            status=OrderComment.Status.DELETED,
        )

        response = self.client.get(
            self._public_delivery_detail_url(self.public_delivery)
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["public_comments_count"], 1)

    def test_public_comments_count_does_not_include_other_delivery_comments(self):
        OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.public_delivery,
            text="Approved comment on main delivery",
            status=OrderComment.Status.APPROVED,
        )

        OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.other_public_delivery,
            text="Approved comment on other delivery",
            status=OrderComment.Status.APPROVED,
        )

        response = self.client.get(
            self._public_delivery_detail_url(self.public_delivery)
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["public_comments_count"], 1)


class PublicOrderDeliveryCommentCountAnnotationTests(APITestCase):
    def setUp(self):
        User = get_user_model()

        self.client_user = User.objects.create_user(
            username="public-count-annotation-client",
            password="pass12345",
            role="client",
        )
        self.editor_user = User.objects.create_user(
            username="public-count-annotation-editor",
            password="pass12345",
            role="editor",
        )

        self.order = Order.objects.create(
            client=self.client_user,
            editor=self.editor_user,
            title="Public Count Annotation Order",
            description="Testing annotated public comment counts",
            status=Order.Status.DELIVERED,
        )

        self.delivery = OrderDelivery.objects.create(
            order=self.order,
            uploaded_by=self.editor_user,
            file=SimpleUploadedFile(
                "public-count-annotation-delivery.jpg",
                b"public-count-annotation-delivery-content",
                content_type="image/jpeg",
            ),
            note="Annotated public comment count",
            publication_status=OrderDelivery.PublicationStatus.APPROVED,
        )

    def _public_deliveries_url(self):
        return reverse("orders-public-deliveries")

    def _public_delivery_detail_url(self):
        return reverse(
            "orders-public-delivery-detail",
            kwargs={"delivery_id": self.delivery.id},
        )

    def test_public_delivery_list_uses_annotated_public_comments_count(self):
        OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.delivery,
            text="Approved public comment one",
            status=OrderComment.Status.APPROVED,
        )
        OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.delivery,
            text="Approved public comment two",
            status=OrderComment.Status.APPROVED,
        )
        OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.delivery,
            text="Active comment not public",
            status=OrderComment.Status.ACTIVE,
        )

        response = self.client.get(self._public_deliveries_url())

        self.assertEqual(response.status_code, 200)

        item = next(item for item in response.data if item["id"] == self.delivery.id)

        self.assertEqual(item["public_comments_count"], 2)

    def test_public_delivery_detail_uses_annotated_public_comments_count(self):
        OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.delivery,
            text="Approved public comment",
            status=OrderComment.Status.APPROVED,
        )
        OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.delivery,
            text="Deleted comment not public",
            status=OrderComment.Status.DELETED,
        )

        response = self.client.get(self._public_delivery_detail_url())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["public_comments_count"], 1)


class PublicOrderDeliveryPaginationBehaviorTests(APITestCase):
    def setUp(self):
        User = get_user_model()

        self.client_user = User.objects.create_user(
            username="public-pagination-client",
            password="pass12345",
            role="client",
        )
        self.editor_user = User.objects.create_user(
            username="public-pagination-editor",
            password="pass12345",
            role="editor",
        )

        self.order = Order.objects.create(
            client=self.client_user,
            editor=self.editor_user,
            title="Public Pagination Order",
            description="Testing public deliveries pagination behavior",
            status=Order.Status.DELIVERED,
        )

        for index in range(3):
            OrderDelivery.objects.create(
                order=self.order,
                uploaded_by=self.editor_user,
                file=SimpleUploadedFile(
                    f"public-pagination-{index}.jpg",
                    f"public-pagination-content-{index}".encode(),
                    content_type="image/jpeg",
                ),
                note=f"Public pagination delivery {index}",
                publication_status=OrderDelivery.PublicationStatus.APPROVED,
            )

    def _public_deliveries_url(self):
        return reverse("orders-public-deliveries")

    def test_public_deliveries_accepts_pagination_query_params(self):
        response = self.client.get(
            self._public_deliveries_url(),
            {
                "page": 1,
                "page_size": 2,
            },
        )

        self.assertEqual(response.status_code, 200)

        if isinstance(response.data, dict) and "results" in response.data:
            self.assertIn("count", response.data)
            self.assertIn("results", response.data)
            self.assertLessEqual(len(response.data["results"]), 2)
        else:
            self.assertEqual(len(response.data), 3)


class PublicEditorPortfolioAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()

        self.client_user = User.objects.create_user(
            username="portfolio-client",
            password="pass12345",
            role="client",
        )
        self.editor_user = User.objects.create_user(
            username="portfolio-editor",
            password="pass12345",
            role="editor",
            first_name="Portfolio",
            last_name="Editor",
        )
        self.other_editor = User.objects.create_user(
            username="portfolio-other-editor",
            password="pass12345",
            role="editor",
        )

        self.order = Order.objects.create(
            client=self.client_user,
            editor=self.editor_user,
            title="Portfolio Main Order",
            description="Testing editor portfolio",
            status=Order.Status.DELIVERED,
        )

        self.other_order = Order.objects.create(
            client=self.client_user,
            editor=self.other_editor,
            title="Portfolio Other Order",
            description="Testing other editor portfolio",
            status=Order.Status.DELIVERED,
        )

        self.public_delivery_one = OrderDelivery.objects.create(
            order=self.order,
            uploaded_by=self.editor_user,
            file=SimpleUploadedFile(
                "portfolio-public-one.jpg",
                b"portfolio-public-one-content",
                content_type="image/jpeg",
            ),
            note="Portfolio public delivery one",
            publication_status=OrderDelivery.PublicationStatus.APPROVED,
        )

        self.public_delivery_two = OrderDelivery.objects.create(
            order=self.order,
            uploaded_by=self.editor_user,
            file=SimpleUploadedFile(
                "portfolio-public-two.jpg",
                b"portfolio-public-two-content",
                content_type="image/jpeg",
            ),
            note="Portfolio public delivery two",
            publication_status=OrderDelivery.PublicationStatus.APPROVED,
        )

        self.private_delivery = OrderDelivery.objects.create(
            order=self.order,
            uploaded_by=self.editor_user,
            file=SimpleUploadedFile(
                "portfolio-private.jpg",
                b"portfolio-private-content",
                content_type="image/jpeg",
            ),
            note="Portfolio private delivery",
            publication_status=OrderDelivery.PublicationStatus.PRIVATE,
        )

        self.other_editor_delivery = OrderDelivery.objects.create(
            order=self.other_order,
            uploaded_by=self.other_editor,
            file=SimpleUploadedFile(
                "portfolio-other-editor.jpg",
                b"portfolio-other-editor-content",
                content_type="image/jpeg",
            ),
            note="Other editor public delivery",
            publication_status=OrderDelivery.PublicationStatus.APPROVED,
        )

        OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.public_delivery_one,
            text="Approved portfolio comment one",
            status=OrderComment.Status.APPROVED,
        )

        OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.public_delivery_one,
            text="Approved portfolio comment two",
            status=OrderComment.Status.APPROVED,
        )

        OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.public_delivery_two,
            text="Active portfolio comment not public",
            status=OrderComment.Status.ACTIVE,
        )

    def _portfolio_url(self, editor):
        return reverse(
            "orders-public-editor-portfolio",
            kwargs={"editor_id": editor.id},
        )

    def test_anonymous_user_can_retrieve_public_editor_portfolio(self):
        response = self.client.get(self._portfolio_url(self.editor_user))

        self.assertEqual(response.status_code, 200)

    def test_public_editor_portfolio_contains_editor_info(self):
        response = self.client.get(self._portfolio_url(self.editor_user))

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data["editor"]["id"], self.editor_user.id)
        self.assertEqual(
            response.data["editor"]["username"],
            self.editor_user.username,
        )
        self.assertEqual(response.data["editor"]["first_name"], "Portfolio")
        self.assertEqual(response.data["editor"]["last_name"], "Editor")

    def test_public_editor_portfolio_returns_only_editor_public_deliveries(self):
        response = self.client.get(self._portfolio_url(self.editor_user))

        self.assertEqual(response.status_code, 200)

        deliveries = response.data["deliveries"]

        if isinstance(deliveries, dict) and "results" in deliveries:
            delivery_items = deliveries["results"]
        else:
            delivery_items = deliveries

        returned_ids = {item["id"] for item in delivery_items}

        self.assertIn(self.public_delivery_one.id, returned_ids)
        self.assertIn(self.public_delivery_two.id, returned_ids)
        self.assertNotIn(self.private_delivery.id, returned_ids)
        self.assertNotIn(self.other_editor_delivery.id, returned_ids)
        self.assertEqual(len(returned_ids), 2)

    def test_public_editor_portfolio_contains_stats(self):
        response = self.client.get(self._portfolio_url(self.editor_user))

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data["stats"]["public_deliveries_count"], 2)
        self.assertEqual(response.data["stats"]["public_comments_count"], 2)

    def test_public_editor_portfolio_returns_404_for_missing_editor(self):
        response = self.client.get(
            reverse(
                "orders-public-editor-portfolio",
                kwargs={"editor_id": 999999},
            )
        )

        self.assertEqual(response.status_code, 404)


class PublicEditorPortfolioPolishTests(APITestCase):
    def setUp(self):
        User = get_user_model()

        self.client_user = User.objects.create_user(
            username="portfolio-polish-client",
            password="pass12345",
            role="client",
        )
        self.editor_user = User.objects.create_user(
            username="portfolio-polish-editor",
            password="pass12345",
            role="editor",
            first_name="Safe",
            last_name="Editor",
        )
        self.empty_editor = User.objects.create_user(
            username="portfolio-empty-editor",
            password="pass12345",
            role="editor",
        )
        self.non_editor_user = User.objects.create_user(
            username="portfolio-non-editor",
            password="pass12345",
            role="client",
        )

        self.order = Order.objects.create(
            client=self.client_user,
            editor=self.editor_user,
            title="Portfolio Polish Order",
            description="Testing portfolio polish behavior",
            status=Order.Status.DELIVERED,
        )

        self.first_delivery = OrderDelivery.objects.create(
            order=self.order,
            uploaded_by=self.editor_user,
            file=SimpleUploadedFile(
                "portfolio-polish-first.jpg",
                b"portfolio-polish-first-content",
                content_type="image/jpeg",
            ),
            note="First portfolio polish delivery",
            publication_status=OrderDelivery.PublicationStatus.APPROVED,
        )

        self.second_delivery = OrderDelivery.objects.create(
            order=self.order,
            uploaded_by=self.editor_user,
            file=SimpleUploadedFile(
                "portfolio-polish-second.jpg",
                b"portfolio-polish-second-content",
                content_type="image/jpeg",
            ),
            note="Second portfolio polish delivery",
            publication_status=OrderDelivery.PublicationStatus.APPROVED,
        )

        self.private_delivery = OrderDelivery.objects.create(
            order=self.order,
            uploaded_by=self.editor_user,
            file=SimpleUploadedFile(
                "portfolio-polish-private.jpg",
                b"portfolio-polish-private-content",
                content_type="image/jpeg",
            ),
            note="Private portfolio polish delivery",
            publication_status=OrderDelivery.PublicationStatus.PRIVATE,
        )

        self.second_private_delivery = OrderDelivery.objects.create(
            order=self.order,
            uploaded_by=self.editor_user,
            file=SimpleUploadedFile(
                "portfolio-polish-private-second.jpg",
                b"portfolio-polish-private-second-content",
                content_type="image/jpeg",
            ),
            note="Second private portfolio polish delivery",
            publication_status=OrderDelivery.PublicationStatus.PRIVATE,
        )

        OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.second_delivery,
            text="Approved comment one",
            status=OrderComment.Status.APPROVED,
        )
        OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.second_delivery,
            text="Approved comment two",
            status=OrderComment.Status.APPROVED,
        )
        OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.first_delivery,
            text="Approved comment three",
            status=OrderComment.Status.APPROVED,
        )

    def _portfolio_url(self, editor):
        return reverse(
            "orders-public-editor-portfolio",
            kwargs={"editor_id": editor.id},
        )

    def test_public_editor_portfolio_returns_404_for_non_editor_user(self):
        response = self.client.get(self._portfolio_url(self.non_editor_user))

        self.assertEqual(response.status_code, 404)

    def test_public_editor_portfolio_allows_editor_with_no_public_deliveries(self):
        response = self.client.get(self._portfolio_url(self.empty_editor))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["stats"]["public_deliveries_count"], 0)
        self.assertEqual(response.data["stats"]["public_comments_count"], 0)
        self.assertEqual(response.data["deliveries"], [])

    def test_public_editor_portfolio_does_not_expose_non_public_deliveries(self):
        response = self.client.get(self._portfolio_url(self.editor_user))

        self.assertEqual(response.status_code, 200)

        returned_ids = {item["id"] for item in response.data["deliveries"]}

        self.assertIn(self.first_delivery.id, returned_ids)
        self.assertIn(self.second_delivery.id, returned_ids)
        self.assertNotIn(self.private_delivery.id, returned_ids)
        self.assertNotIn(self.second_private_delivery.id, returned_ids)

    def test_public_editor_portfolio_exposes_only_safe_editor_fields(self):
        response = self.client.get(self._portfolio_url(self.editor_user))

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            set(response.data["editor"].keys()),
            {"id", "username", "first_name", "last_name"},
        )

    def test_public_editor_portfolio_supports_most_commented_ordering(self):
        response = self.client.get(
            self._portfolio_url(self.editor_user),
            {"ordering": "most_commented"},
        )

        self.assertEqual(response.status_code, 200)

        delivery_ids = [item["id"] for item in response.data["deliveries"]]

        self.assertEqual(delivery_ids[0], self.second_delivery.id)
        self.assertEqual(delivery_ids[1], self.first_delivery.id)

    def test_public_editor_portfolio_supports_oldest_ordering(self):
        response = self.client.get(
            self._portfolio_url(self.editor_user),
            {"ordering": "oldest"},
        )

        self.assertEqual(response.status_code, 200)

        delivery_ids = [item["id"] for item in response.data["deliveries"]]

        self.assertEqual(
            set(delivery_ids),
            {self.first_delivery.id, self.second_delivery.id},
        )


class PublicEditorPortfolioRatingSummaryTests(APITestCase):
    def setUp(self):
        User = get_user_model()

        self.client_user = User.objects.create_user(
            username="portfolio-rating-client",
            password="pass12345",
            role="client",
        )
        self.supervisor_user = User.objects.create_user(
            username="portfolio-rating-supervisor",
            password="pass12345",
            role="supervisor",
        )
        self.editor_user = User.objects.create_user(
            username="portfolio-rating-editor",
            password="pass12345",
            role="editor",
        )
        self.other_editor = User.objects.create_user(
            username="portfolio-rating-other-editor",
            password="pass12345",
            role="editor",
        )

        self.public_order = Order.objects.create(
            client=self.client_user,
            editor=self.editor_user,
            title="Portfolio Rating Public Order",
            description="Public order for rating summary",
            status=Order.Status.DELIVERED,
        )

        self.second_public_order = Order.objects.create(
            client=self.client_user,
            editor=self.editor_user,
            title="Portfolio Rating Second Public Order",
            description="Second public order for rating summary",
            status=Order.Status.DELIVERED,
        )

        self.private_order = Order.objects.create(
            client=self.client_user,
            editor=self.editor_user,
            title="Portfolio Rating Private Order",
            description="Private order should not affect public rating",
            status=Order.Status.DELIVERED,
        )

        self.other_editor_order = Order.objects.create(
            client=self.client_user,
            editor=self.other_editor,
            title="Portfolio Rating Other Editor Order",
            description="Other editor order should not affect rating",
            status=Order.Status.DELIVERED,
        )

        self.public_delivery = OrderDelivery.objects.create(
            order=self.public_order,
            uploaded_by=self.editor_user,
            file=SimpleUploadedFile(
                "portfolio-rating-public.jpg",
                b"portfolio-rating-public-content",
                content_type="image/jpeg",
            ),
            note="Public delivery for rating",
            publication_status=OrderDelivery.PublicationStatus.APPROVED,
        )

        self.second_public_delivery = OrderDelivery.objects.create(
            order=self.second_public_order,
            uploaded_by=self.editor_user,
            file=SimpleUploadedFile(
                "portfolio-rating-public-second.jpg",
                b"portfolio-rating-public-second-content",
                content_type="image/jpeg",
            ),
            note="Second public delivery for rating",
            publication_status=OrderDelivery.PublicationStatus.APPROVED,
        )

        self.private_delivery = OrderDelivery.objects.create(
            order=self.private_order,
            uploaded_by=self.editor_user,
            file=SimpleUploadedFile(
                "portfolio-rating-private.jpg",
                b"portfolio-rating-private-content",
                content_type="image/jpeg",
            ),
            note="Private delivery for rating",
            publication_status=OrderDelivery.PublicationStatus.PRIVATE,
        )

        self.other_editor_delivery = OrderDelivery.objects.create(
            order=self.other_editor_order,
            uploaded_by=self.other_editor,
            file=SimpleUploadedFile(
                "portfolio-rating-other-editor.jpg",
                b"portfolio-rating-other-editor-content",
                content_type="image/jpeg",
            ),
            note="Other editor public delivery for rating",
            publication_status=OrderDelivery.PublicationStatus.APPROVED,
        )

        OrderRating.objects.create(
            order=self.public_order,
            rated_by=self.client_user,
            source="client",
            score=5,
            comment="Great public work",
        )

        OrderRating.objects.create(
            order=self.second_public_order,
            rated_by=self.supervisor_user,
            source="supervisor",
            score=3,
            comment="Good public work",
        )

        OrderRating.objects.create(
            order=self.private_order,
            rated_by=self.client_user,
            source="client",
            score=1,
            comment="Private order rating should not be public",
        )

        OrderRating.objects.create(
            order=self.other_editor_order,
            rated_by=self.client_user,
            source="client",
            score=1,
            comment="Other editor rating should not affect this editor",
        )

    def _portfolio_url(self, editor):
        return reverse(
            "orders-public-editor-portfolio",
            kwargs={"editor_id": editor.id},
        )

    def test_public_editor_portfolio_contains_rating_summary(self):
        response = self.client.get(self._portfolio_url(self.editor_user))

        self.assertEqual(response.status_code, 200)
        self.assertIn("rating", response.data)
        self.assertIn("average", response.data["rating"])
        self.assertIn("count", response.data["rating"])

    def test_public_editor_portfolio_rating_summary_calculates_average(self):
        response = self.client.get(self._portfolio_url(self.editor_user))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["rating"]["average"], 4.0)

    def test_public_editor_portfolio_rating_summary_calculates_count(self):
        response = self.client.get(self._portfolio_url(self.editor_user))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["rating"]["count"], 2)

    def test_public_editor_portfolio_rating_excludes_orders_without_public_delivery(
        self,
    ):
        response = self.client.get(self._portfolio_url(self.editor_user))

        self.assertEqual(response.status_code, 200)

        # If private_order rating with score=1 was included,
        # average would be 3.0 instead of 4.0 and count would be 3.
        self.assertEqual(response.data["rating"]["average"], 4.0)
        self.assertEqual(response.data["rating"]["count"], 2)

    def test_public_editor_portfolio_rating_excludes_other_editor_ratings(self):
        response = self.client.get(self._portfolio_url(self.editor_user))

        self.assertEqual(response.status_code, 200)

        # Other editor rating score=1 must not affect this editor.
        self.assertEqual(response.data["rating"]["average"], 4.0)
        self.assertEqual(response.data["rating"]["count"], 2)

    def test_public_editor_portfolio_rating_returns_zero_for_editor_without_ratings(
        self,
    ):
        empty_editor = get_user_model().objects.create_user(
            username="portfolio-rating-empty-editor",
            password="pass12345",
            role="editor",
        )

        response = self.client.get(self._portfolio_url(empty_editor))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["rating"]["average"], 0)
        self.assertEqual(response.data["rating"]["count"], 0)

class PublicEditorPortfolioResponsePolishTests(APITestCase):
    def setUp(self):
        User = get_user_model()

        self.client_user = User.objects.create_user(
            username="portfolio-response-client",
            password="pass12345",
            role="client",
        )
        self.editor_user = User.objects.create_user(
            username="portfolio-response-editor",
            password="pass12345",
            role="editor",
        )

        self.first_order = Order.objects.create(
            client=self.client_user,
            editor=self.editor_user,
            title="Portfolio Response First Order",
            description="First public order",
            status=Order.Status.DELIVERED,
        )

        self.second_order = Order.objects.create(
            client=self.client_user,
            editor=self.editor_user,
            title="Portfolio Response Second Order",
            description="Second public order",
            status=Order.Status.DELIVERED,
        )

        self.first_delivery = OrderDelivery.objects.create(
            order=self.first_order,
            uploaded_by=self.editor_user,
            file=SimpleUploadedFile(
                "portfolio-response-first.jpg",
                b"portfolio-response-first-content",
                content_type="image/jpeg",
            ),
            note="First public delivery",
            publication_status=OrderDelivery.PublicationStatus.APPROVED,
        )

        self.second_delivery = OrderDelivery.objects.create(
            order=self.second_order,
            uploaded_by=self.editor_user,
            file=SimpleUploadedFile(
                "portfolio-response-second.jpg",
                b"portfolio-response-second-content",
                content_type="image/jpeg",
            ),
            note="Second public delivery",
            publication_status=OrderDelivery.PublicationStatus.APPROVED,
        )

    def _portfolio_url(self):
        return reverse(
            "orders-public-editor-portfolio",
            kwargs={"editor_id": self.editor_user.id},
        )

    def test_public_editor_portfolio_contains_public_orders_count(self):
        response = self.client.get(self._portfolio_url())

        self.assertEqual(response.status_code, 200)
        self.assertIn("public_orders_count", response.data["stats"])
        self.assertEqual(response.data["stats"]["public_orders_count"], 2)

    def test_public_editor_portfolio_contains_meta(self):
        response = self.client.get(self._portfolio_url())

        self.assertEqual(response.status_code, 200)
        self.assertIn("meta", response.data)
        self.assertEqual(response.data["meta"]["ordering"], "newest")
        self.assertEqual(
            response.data["meta"]["available_orderings"],
            ["newest", "oldest", "most_commented"],
        )

    def test_public_editor_portfolio_meta_reflects_requested_ordering(self):
        response = self.client.get(
            self._portfolio_url(),
            {"ordering": "oldest"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["meta"]["ordering"], "oldest")

    def test_public_editor_portfolio_invalid_ordering_falls_back_to_newest(self):
        response = self.client.get(
            self._portfolio_url(),
            {"ordering": "invalid-ordering"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["meta"]["ordering"], "newest")

class PublicEditorPortfolioContractAndEdgeCaseTests(APITestCase):
    def setUp(self):
        User = get_user_model()

        self.client_user = User.objects.create_user(
            username="portfolio-contract-client",
            password="pass12345",
            role="client",
        )
        self.editor_user = User.objects.create_user(
            username="portfolio-contract-editor",
            password="pass12345",
            role="editor",
            first_name="Contract",
            last_name="Editor",
        )
        self.empty_editor = User.objects.create_user(
            username="portfolio-contract-empty-editor",
            password="pass12345",
            role="editor",
        )
        self.non_editor_user = User.objects.create_user(
            username="portfolio-contract-non-editor",
            password="pass12345",
            role="client",
        )

        self.order = Order.objects.create(
            client=self.client_user,
            editor=self.editor_user,
            title="Portfolio Contract Order",
            description="Order used for portfolio contract tests",
            status=Order.Status.DELIVERED,
        )

        self.public_delivery = OrderDelivery.objects.create(
            order=self.order,
            uploaded_by=self.editor_user,
            file=SimpleUploadedFile(
                "portfolio-contract-public.jpg",
                b"portfolio-contract-public-content",
                content_type="image/jpeg",
            ),
            note="Public delivery for portfolio contract",
            publication_status=OrderDelivery.PublicationStatus.APPROVED,
        )

        self.private_delivery = OrderDelivery.objects.create(
            order=self.order,
            uploaded_by=self.editor_user,
            file=SimpleUploadedFile(
                "portfolio-contract-private.jpg",
                b"portfolio-contract-private-content",
                content_type="image/jpeg",
            ),
            note="Private delivery should not appear in public portfolio",
            publication_status=OrderDelivery.PublicationStatus.PRIVATE,
        )

        OrderRating.objects.create(
            order=self.order,
            rated_by=self.client_user,
            source="client",
            score=5,
            comment="Great public portfolio contract work",
        )

        OrderComment.objects.create(
            order=self.order,
            sender=self.client_user,
            target_type=OrderComment.TargetType.DELIVERY,
            delivery=self.public_delivery,
            text="Approved public contract comment",
            status=OrderComment.Status.APPROVED,
        )

    def _portfolio_url(self, editor_id):
        return reverse(
            "orders-public-editor-portfolio",
            kwargs={"editor_id": editor_id},
        )

    def test_public_editor_portfolio_response_contract_top_level_keys(self):
        response = self.client.get(self._portfolio_url(self.editor_user.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.data.keys()),
            {"editor", "stats", "rating", "meta", "deliveries"},
        )

    def test_public_editor_portfolio_response_contract_editor_keys(self):
        response = self.client.get(self._portfolio_url(self.editor_user.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.data["editor"].keys()),
            {"id", "username", "first_name", "last_name"},
        )

    def test_public_editor_portfolio_response_contract_stats_keys(self):
        response = self.client.get(self._portfolio_url(self.editor_user.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.data["stats"].keys()),
            {
                "public_deliveries_count",
                "public_comments_count",
                "public_orders_count",
            },
        )

    def test_public_editor_portfolio_response_contract_rating_keys(self):
        response = self.client.get(self._portfolio_url(self.editor_user.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.data["rating"].keys()),
            {"average", "count"},
        )

    def test_public_editor_portfolio_response_contract_meta_keys(self):
        response = self.client.get(self._portfolio_url(self.editor_user.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.data["meta"].keys()),
            {"ordering", "available_orderings"},
        )

    def test_public_editor_portfolio_empty_editor_contract(self):
        response = self.client.get(self._portfolio_url(self.empty_editor.id))

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data["stats"],
            {
                "public_deliveries_count": 0,
                "public_comments_count": 0,
                "public_orders_count": 0,
            },
        )
        self.assertEqual(
            response.data["rating"],
            {
                "average": 0,
                "count": 0,
            },
        )
        self.assertEqual(
            response.data["meta"],
            {
                "ordering": "newest",
                "available_orderings": [
                    "newest",
                    "oldest",
                    "most_commented",
                ],
            },
        )
        self.assertEqual(response.data["deliveries"], [])

    def test_public_editor_portfolio_unknown_editor_returns_404(self):
        response = self.client.get(self._portfolio_url(999999))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["detail"], "Editor not found.")

    def test_public_editor_portfolio_non_editor_returns_404(self):
        response = self.client.get(self._portfolio_url(self.non_editor_user.id))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["detail"], "Editor not found.")

    def test_public_editor_portfolio_invalid_ordering_keeps_contract(self):
        response = self.client.get(
            self._portfolio_url(self.editor_user.id),
            {"ordering": "bad-value"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["meta"]["ordering"], "newest")
        self.assertEqual(
            response.data["meta"]["available_orderings"],
            ["newest", "oldest", "most_commented"],
        )

    def test_public_editor_portfolio_does_not_expose_private_delivery_in_contract(self):
        response = self.client.get(self._portfolio_url(self.editor_user.id))

        self.assertEqual(response.status_code, 200)

        delivery_ids = {item["id"] for item in response.data["deliveries"]}

        self.assertIn(self.public_delivery.id, delivery_ids)
        self.assertNotIn(self.private_delivery.id, delivery_ids)
