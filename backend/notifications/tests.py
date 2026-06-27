from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Notification


class NotificationModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="notification_user",
            password="TestPass123!",
        )
        self.actor = get_user_model().objects.create_user(
            username="notification_actor",
            password="TestPass123!",
        )

    def test_create_notification_with_defaults(self):
        notification = Notification.objects.create(
            recipient=self.user,
            actor=self.actor,
            notification_type=Notification.Type.PROJECT_REQUEST,
            title="New project proposal",
            message="An editor submitted a proposal.",
            data={
                "project_request_id": 1,
                "proposal_id": 2,
            },
        )

        self.assertEqual(notification.recipient, self.user)
        self.assertEqual(notification.actor, self.actor)
        self.assertEqual(
            notification.notification_type, Notification.Type.PROJECT_REQUEST
        )
        self.assertEqual(notification.priority, Notification.Priority.NORMAL)
        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)
        self.assertEqual(notification.data["project_request_id"], 1)
        self.assertEqual(notification.data["proposal_id"], 2)

    def test_mark_as_read_sets_read_at(self):
        notification = Notification.objects.create(
            recipient=self.user,
            title="Read me",
            message="This notification should be marked as read.",
        )

        notification.mark_as_read()
        notification.refresh_from_db()

        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)

    def test_mark_as_read_is_idempotent(self):
        notification = Notification.objects.create(
            recipient=self.user,
            title="Read once",
        )

        notification.mark_as_read()
        first_read_at = notification.read_at

        notification.mark_as_read()
        notification.refresh_from_db()

        self.assertTrue(notification.is_read)
        self.assertEqual(notification.read_at, first_read_at)

    def test_mark_as_unread_clears_read_at(self):
        notification = Notification.objects.create(
            recipient=self.user,
            title="Unread me",
        )

        notification.mark_as_read()
        notification.mark_as_unread()
        notification.refresh_from_db()

        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)

    def test_notifications_are_ordered_latest_first(self):
        first = Notification.objects.create(
            recipient=self.user,
            title="First notification",
        )
        second = Notification.objects.create(
            recipient=self.user,
            title="Second notification",
        )

        notifications = list(Notification.objects.all())

        self.assertEqual(notifications[0], second)
        self.assertEqual(notifications[1], first)

    def test_deleting_recipient_deletes_notifications(self):
        notification = Notification.objects.create(
            recipient=self.user,
            title="Should be deleted with user",
        )

        self.assertEqual(Notification.objects.count(), 1)

        self.user.delete()

        self.assertEqual(Notification.objects.count(), 0)

    def test_deleting_actor_keeps_notification_with_null_actor(self):
        notification = Notification.objects.create(
            recipient=self.user,
            actor=self.actor,
            title="Actor can be deleted",
        )

        self.actor.delete()

        notification.refresh_from_db()

        self.assertIsNone(notification.actor)
        self.assertEqual(Notification.objects.count(), 1)


from rest_framework import status
from rest_framework.test import APITestCase


class NotificationAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="api_notification_user",
            password="TestPass123!",
        )
        self.other_user = get_user_model().objects.create_user(
            username="api_notification_other_user",
            password="TestPass123!",
        )
        self.actor = get_user_model().objects.create_user(
            username="api_notification_actor",
            password="TestPass123!",
        )

    def get_results(self, response):
        if isinstance(response.data, dict) and "results" in response.data:
            return response.data["results"]
        return response.data

    def test_authenticated_user_can_list_own_notifications(self):
        own_notification = Notification.objects.create(
            recipient=self.user,
            actor=self.actor,
            notification_type=Notification.Type.PROJECT_REQUEST,
            title="Own notification",
            message="This belongs to the authenticated user.",
            data={"project_request_id": 1},
        )
        Notification.objects.create(
            recipient=self.other_user,
            actor=self.actor,
            notification_type=Notification.Type.SYSTEM,
            title="Other notification",
            message="This should not be visible.",
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/notifications/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = self.get_results(response)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], own_notification.id)
        self.assertEqual(results[0]["title"], "Own notification")
        self.assertEqual(results[0]["recipient"], self.user.id)
        self.assertEqual(results[0]["recipient_username"], self.user.username)
        self.assertEqual(results[0]["actor"], self.actor.id)
        self.assertEqual(results[0]["actor_username"], self.actor.username)

    def test_unauthenticated_user_cannot_list_notifications(self):
        response = self.client.get("/api/notifications/")

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_authenticated_user_can_retrieve_own_notification(self):
        notification = Notification.objects.create(
            recipient=self.user,
            actor=self.actor,
            notification_type=Notification.Type.PROPOSAL,
            title="Retrieve notification",
            message="Retrieve detail.",
            data={"proposal_id": 10},
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.get(f"/api/notifications/{notification.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], notification.id)
        self.assertEqual(response.data["title"], "Retrieve notification")
        self.assertEqual(response.data["data"]["proposal_id"], 10)

    def test_user_cannot_retrieve_other_users_notification(self):
        notification = Notification.objects.create(
            recipient=self.other_user,
            actor=self.actor,
            title="Private notification",
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.get(f"/api/notifications/{notification.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unread_count_returns_only_authenticated_users_unread_notifications(self):
        Notification.objects.create(
            recipient=self.user,
            title="Unread one",
            is_read=False,
        )
        Notification.objects.create(
            recipient=self.user,
            title="Unread two",
            is_read=False,
        )
        Notification.objects.create(
            recipient=self.user,
            title="Already read",
            is_read=True,
        )
        Notification.objects.create(
            recipient=self.other_user,
            title="Other unread",
            is_read=False,
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/notifications/unread-count/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["unread_count"], 2)

    def test_user_can_mark_own_notification_as_read(self):
        notification = Notification.objects.create(
            recipient=self.user,
            title="Mark read notification",
            is_read=False,
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.post(f"/api/notifications/{notification.id}/mark-read/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        notification.refresh_from_db()

        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)
        self.assertTrue(response.data["is_read"])

    def test_mark_read_is_idempotent(self):
        notification = Notification.objects.create(
            recipient=self.user,
            title="Idempotent mark read",
            is_read=False,
        )

        self.client.force_authenticate(user=self.user)

        first_response = self.client.post(
            f"/api/notifications/{notification.id}/mark-read/"
        )
        notification.refresh_from_db()
        first_read_at = notification.read_at

        second_response = self.client.post(
            f"/api/notifications/{notification.id}/mark-read/"
        )
        notification.refresh_from_db()

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertTrue(notification.is_read)
        self.assertEqual(notification.read_at, first_read_at)

    def test_user_can_mark_own_notification_as_unread(self):
        notification = Notification.objects.create(
            recipient=self.user,
            title="Mark unread notification",
        )
        notification.mark_as_read()

        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            f"/api/notifications/{notification.id}/mark-unread/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        notification.refresh_from_db()

        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)
        self.assertFalse(response.data["is_read"])

    def test_user_cannot_mark_other_users_notification_as_read(self):
        notification = Notification.objects.create(
            recipient=self.other_user,
            title="Other user notification",
            is_read=False,
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.post(f"/api/notifications/{notification.id}/mark-read/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        notification.refresh_from_db()

        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)

    def test_user_can_mark_all_own_notifications_as_read(self):
        first = Notification.objects.create(
            recipient=self.user,
            title="First unread",
            is_read=False,
        )
        second = Notification.objects.create(
            recipient=self.user,
            title="Second unread",
            is_read=False,
        )
        already_read = Notification.objects.create(
            recipient=self.user,
            title="Already read",
            is_read=True,
        )
        other_notification = Notification.objects.create(
            recipient=self.other_user,
            title="Other unread",
            is_read=False,
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.post("/api/notifications/mark-all-read/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["updated_count"], 2)

        first.refresh_from_db()
        second.refresh_from_db()
        already_read.refresh_from_db()
        other_notification.refresh_from_db()

        self.assertTrue(first.is_read)
        self.assertTrue(second.is_read)
        self.assertTrue(already_read.is_read)
        self.assertFalse(other_notification.is_read)

        self.assertIsNotNone(first.read_at)
        self.assertIsNotNone(second.read_at)

    def test_notification_list_returns_latest_first(self):
        first = Notification.objects.create(
            recipient=self.user,
            title="First API notification",
        )
        second = Notification.objects.create(
            recipient=self.user,
            title="Second API notification",
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/notifications/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = self.get_results(response)

        self.assertEqual(results[0]["id"], second.id)
        self.assertEqual(results[1]["id"], first.id)
