from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone

from .models import Notification

from .services import (
    create_notification,
    create_notifications,
    mark_user_notifications_as_read,
    notify_staff_users,
)


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
    
    def test_notification_summary_returns_counts_for_authenticated_user(self):
        Notification.objects.create(
            recipient=self.user,
            notification_type=Notification.Type.SYSTEM,
            priority=Notification.Priority.NORMAL,
            title="System unread",
            is_read=False,
        )
        Notification.objects.create(
            recipient=self.user,
            notification_type=Notification.Type.PROPOSAL,
            priority=Notification.Priority.HIGH,
            title="Proposal unread high",
            is_read=False,
        )
        Notification.objects.create(
            recipient=self.user,
            notification_type=Notification.Type.PROPOSAL,
            priority=Notification.Priority.NORMAL,
            title="Proposal read",
            is_read=True,
        )
        Notification.objects.create(
            recipient=self.user,
            notification_type=Notification.Type.ORDER,
            priority=Notification.Priority.NORMAL,
            title="Order read",
            is_read=True,
        )
        Notification.objects.create(
            recipient=self.other_user,
            notification_type=Notification.Type.PROPOSAL,
            priority=Notification.Priority.HIGH,
            title="Other user notification",
            is_read=False,
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/notifications/summary/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["total_count"], 4)
        self.assertEqual(response.data["unread_count"], 2)
        self.assertEqual(response.data["read_count"], 2)
        self.assertEqual(response.data["high_priority_unread_count"], 1)

        self.assertEqual(response.data["by_type"][Notification.Type.SYSTEM], 1)
        self.assertEqual(response.data["by_type"][Notification.Type.PROPOSAL], 2)
        self.assertEqual(response.data["by_type"][Notification.Type.ORDER], 1)

        self.assertEqual(response.data["by_priority"][Notification.Priority.NORMAL], 3)
        self.assertEqual(response.data["by_priority"][Notification.Priority.HIGH], 1)

    

    def test_mark_selected_notifications_as_read_updates_only_owned_notifications(self):
        first_notification = Notification.objects.create(
            recipient=self.user,
            title="First unread notification",
            is_read=False,
        )
        second_notification = Notification.objects.create(
            recipient=self.user,
            title="Second unread notification",
            is_read=False,
        )
        other_notification = Notification.objects.create(
            recipient=self.other_user,
            title="Other unread notification",
            is_read=False,
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/notifications/mark-selected-read/",
            {
                "ids": [
                    first_notification.id,
                    second_notification.id,
                    other_notification.id,
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["updated_count"], 2)

        first_notification.refresh_from_db()
        second_notification.refresh_from_db()
        other_notification.refresh_from_db()

        self.assertTrue(first_notification.is_read)
        self.assertIsNotNone(first_notification.read_at)

        self.assertTrue(second_notification.is_read)
        self.assertIsNotNone(second_notification.read_at)

        self.assertFalse(other_notification.is_read)
        self.assertIsNone(other_notification.read_at)

    def test_mark_selected_notifications_as_unread_updates_only_owned_notifications(self):
        first_notification = Notification.objects.create(
            recipient=self.user,
            title="First read notification",
            is_read=True,
            read_at=timezone.now(),
        )
        second_notification = Notification.objects.create(
            recipient=self.user,
            title="Second read notification",
            is_read=True,
            read_at=timezone.now(),
        )
        other_notification = Notification.objects.create(
            recipient=self.other_user,
            title="Other read notification",
            is_read=True,
            read_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/notifications/mark-selected-unread/",
            {
                "ids": [
                    first_notification.id,
                    second_notification.id,
                    other_notification.id,
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["updated_count"], 2)

        first_notification.refresh_from_db()
        second_notification.refresh_from_db()
        other_notification.refresh_from_db()

        self.assertFalse(first_notification.is_read)
        self.assertIsNone(first_notification.read_at)

        self.assertFalse(second_notification.is_read)
        self.assertIsNone(second_notification.read_at)

        self.assertTrue(other_notification.is_read)
        self.assertIsNotNone(other_notification.read_at)

    def test_mark_selected_read_rejects_non_list_ids(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/notifications/mark-selected-read/",
            {
                "ids": "not-a-list",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mark_selected_unread_requires_authentication(self):
        response = self.client.post(
            "/api/notifications/mark-selected-unread/",
            {
                "ids": [],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_mark_notification_as_unread_marks_only_owned_notification_unread(self):
        notification = Notification.objects.create(
            recipient=self.user,
            title="Read notification",
            is_read=True,
            read_at=timezone.now(),
        )
        other_notification = Notification.objects.create(
            recipient=self.other_user,
            title="Other read notification",
            is_read=True,
            read_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            f"/api/notifications/{notification.id}/mark-unread/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        notification.refresh_from_db()
        other_notification.refresh_from_db()

        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)

        self.assertTrue(other_notification.is_read)
        self.assertIsNotNone(other_notification.read_at)

    def test_mark_notification_as_unread_does_not_allow_other_users_notification(self):
        other_notification = Notification.objects.create(
            recipient=self.other_user,
            title="Other read notification",
            is_read=True,
            read_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            f"/api/notifications/{other_notification.id}/mark-unread/"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        other_notification.refresh_from_db()

        self.assertTrue(other_notification.is_read)
        self.assertIsNotNone(other_notification.read_at)

    def test_clear_read_notifications_deletes_only_authenticated_users_read_notifications(self):
        first_read = Notification.objects.create(
            recipient=self.user,
            title="First read notification",
            is_read=True,
            read_at=timezone.now(),
        )
        second_read = Notification.objects.create(
            recipient=self.user,
            title="Second read notification",
            is_read=True,
            read_at=timezone.now(),
        )
        unread_notification = Notification.objects.create(
            recipient=self.user,
            title="Unread notification",
            is_read=False,
        )
        other_user_read = Notification.objects.create(
            recipient=self.other_user,
            title="Other user read notification",
            is_read=True,
            read_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.delete("/api/notifications/clear-read/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["deleted_count"], 2)

        self.assertFalse(Notification.objects.filter(id=first_read.id).exists())
        self.assertFalse(Notification.objects.filter(id=second_read.id).exists())

        self.assertTrue(
            Notification.objects.filter(id=unread_notification.id).exists()
        )
        self.assertTrue(
            Notification.objects.filter(id=other_user_read.id).exists()
        )

    def test_clear_read_notifications_requires_authentication(self):
        response = self.client.delete("/api/notifications/clear-read/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_notification_summary_requires_authentication(self):
        response = self.client.get("/api/notifications/summary/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_notification_list_can_filter_by_unread(self):
        unread_notification = Notification.objects.create(
            recipient=self.user,
            notification_type=Notification.Type.SYSTEM,
            title="Unread notification",
            is_read=False,
        )
        Notification.objects.create(
            recipient=self.user,
            notification_type=Notification.Type.SYSTEM,
            title="Read notification",
            is_read=True,
        )
        Notification.objects.create(
            recipient=self.other_user,
            notification_type=Notification.Type.SYSTEM,
            title="Other unread notification",
            is_read=False,
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/notifications/?is_read=false")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = self.get_results(response)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], unread_notification.id)
        self.assertFalse(results[0]["is_read"])

    def test_notification_list_can_filter_by_read(self):
        Notification.objects.create(
            recipient=self.user,
            title="Unread notification",
            is_read=False,
        )
        read_notification = Notification.objects.create(
            recipient=self.user,
            title="Read notification",
            is_read=True,
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/notifications/?is_read=true")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = self.get_results(response)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], read_notification.id)
        self.assertTrue(results[0]["is_read"])

    def test_notification_list_can_filter_by_notification_type(self):
        proposal_notification = Notification.objects.create(
            recipient=self.user,
            notification_type=Notification.Type.PROPOSAL,
            title="Proposal notification",
        )
        Notification.objects.create(
            recipient=self.user,
            notification_type=Notification.Type.SYSTEM,
            title="System notification",
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            f"/api/notifications/?notification_type={Notification.Type.PROPOSAL}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = self.get_results(response)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], proposal_notification.id)
        self.assertEqual(results[0]["notification_type"], Notification.Type.PROPOSAL)

    def test_notification_list_can_filter_by_priority(self):
        high_priority_notification = Notification.objects.create(
            recipient=self.user,
            priority=Notification.Priority.HIGH,
            title="High priority notification",
        )
        Notification.objects.create(
            recipient=self.user,
            priority=Notification.Priority.NORMAL,
            title="Normal priority notification",
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            f"/api/notifications/?priority={Notification.Priority.HIGH}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = self.get_results(response)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], high_priority_notification.id)
        self.assertEqual(results[0]["priority"], Notification.Priority.HIGH)

    def test_notification_list_can_combine_filters(self):
        matching_notification = Notification.objects.create(
            recipient=self.user,
            notification_type=Notification.Type.PROPOSAL,
            priority=Notification.Priority.HIGH,
            title="Matching notification",
            is_read=False,
        )
        Notification.objects.create(
            recipient=self.user,
            notification_type=Notification.Type.PROPOSAL,
            priority=Notification.Priority.NORMAL,
            title="Wrong priority notification",
            is_read=False,
        )
        Notification.objects.create(
            recipient=self.user,
            notification_type=Notification.Type.SYSTEM,
            priority=Notification.Priority.HIGH,
            title="Wrong type notification",
            is_read=False,
        )
        Notification.objects.create(
            recipient=self.user,
            notification_type=Notification.Type.PROPOSAL,
            priority=Notification.Priority.HIGH,
            title="Read matching notification",
            is_read=True,
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            "/api/notifications/"
            f"?is_read=false"
            f"&notification_type={Notification.Type.PROPOSAL}"
            f"&priority={Notification.Priority.HIGH}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = self.get_results(response)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], matching_notification.id)

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

    def test_delete_selected_notifications_deletes_only_owned_notifications(self):
        first_notification = Notification.objects.create(
            recipient=self.user,
            title="First notification",
        )
        second_notification = Notification.objects.create(
            recipient=self.user,
            title="Second notification",
        )
        other_notification = Notification.objects.create(
            recipient=self.other_user,
            title="Other user notification",
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/notifications/delete-selected/",
            {
                "ids": [
                    first_notification.id,
                    second_notification.id,
                    other_notification.id,
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["deleted_count"], 2)

        self.assertFalse(
            Notification.objects.filter(id=first_notification.id).exists()
        )
        self.assertFalse(
            Notification.objects.filter(id=second_notification.id).exists()
        )
        self.assertTrue(
            Notification.objects.filter(id=other_notification.id).exists()
        )

    def test_delete_selected_notifications_rejects_non_list_ids(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/notifications/delete-selected/",
            {
                "ids": "not-a-list",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_selected_notifications_with_empty_ids_returns_zero(self):
        Notification.objects.create(
            recipient=self.user,
            title="User notification",
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/notifications/delete-selected/",
            {
                "ids": [],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["deleted_count"], 0)
        self.assertEqual(Notification.objects.filter(recipient=self.user).count(), 1)

    def test_delete_selected_notifications_requires_authentication(self):
        response = self.client.post(
            "/api/notifications/delete-selected/",
            {
                "ids": [],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_notification_choices_returns_type_and_priority_options(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/notifications/choices/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        type_values = [item["value"] for item in response.data["types"]]
        priority_values = [item["value"] for item in response.data["priorities"]]

        for value, _ in Notification.Type.choices:
            self.assertIn(value, type_values)

        for value, _ in Notification.Priority.choices:
            self.assertIn(value, priority_values)

        self.assertTrue(
            all("label" in item for item in response.data["types"])
        )
        self.assertTrue(
            all("label" in item for item in response.data["priorities"])
        )

    def test_notification_choices_requires_authentication(self):
        response = self.client.get("/api/notifications/choices/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)





class NotificationServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="service_notification_user",
            password="TestPass123!",
        )
        self.other_user = get_user_model().objects.create_user(
            username="service_notification_other_user",
            password="TestPass123!",
        )
        self.actor = get_user_model().objects.create_user(
            username="service_notification_actor",
            password="TestPass123!",
        )
        self.staff_user = get_user_model().objects.create_user(
            username="service_notification_staff",
            password="TestPass123!",
            is_staff=True,
        )
        self.inactive_staff_user = get_user_model().objects.create_user(
            username="service_notification_inactive_staff",
            password="TestPass123!",
            is_staff=True,
            is_active=False,
        )

    def test_create_notification_creates_notification(self):
        notification = create_notification(
            recipient=self.user,
            actor=self.actor,
            notification_type=Notification.Type.PROJECT_REQUEST,
            priority=Notification.Priority.HIGH,
            title="Service notification",
            message="Created through service.",
            data={"project_request_id": 10},
        )

        self.assertIsNotNone(notification)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(notification.recipient, self.user)
        self.assertEqual(notification.actor, self.actor)
        self.assertEqual(
            notification.notification_type, Notification.Type.PROJECT_REQUEST
        )
        self.assertEqual(notification.priority, Notification.Priority.HIGH)
        self.assertEqual(notification.title, "Service notification")
        self.assertEqual(notification.data["project_request_id"], 10)

    def test_create_notification_returns_none_when_recipient_is_none(self):
        notification = create_notification(
            recipient=None,
            title="No recipient",
        )

        self.assertIsNone(notification)
        self.assertEqual(Notification.objects.count(), 0)

    def test_create_notifications_creates_bulk_notifications_for_unique_recipients(
        self,
    ):
        notifications = create_notifications(
            recipients=[
                self.user,
                self.other_user,
                self.user,
                None,
            ],
            actor=self.actor,
            notification_type=Notification.Type.PROPOSAL,
            title="Bulk notification",
            message="Created for multiple users.",
            data={"proposal_id": 20},
        )

        self.assertEqual(len(notifications), 2)
        self.assertEqual(Notification.objects.count(), 2)

        recipients = set(Notification.objects.values_list("recipient", flat=True))

        self.assertEqual(
            recipients,
            {self.user.id, self.other_user.id},
        )

    def test_create_notifications_returns_empty_list_when_no_valid_recipients(self):
        notifications = create_notifications(
            recipients=[None, None],
            title="No valid recipients",
        )

        self.assertEqual(notifications, [])
        self.assertEqual(Notification.objects.count(), 0)

    def test_notify_staff_users_notifies_only_active_staff_users(self):
        create_notification(
            recipient=self.user,
            title="Existing non staff notification",
        )

        notifications = notify_staff_users(
            actor=self.actor,
            notification_type=Notification.Type.SYSTEM,
            priority=Notification.Priority.NORMAL,
            title="Staff notification",
            message="Only active staff should receive this.",
            data={"kind": "staff_alert"},
        )

        self.assertEqual(len(notifications), 1)

        staff_notification = Notification.objects.get(
            title="Staff notification",
        )

        self.assertEqual(staff_notification.recipient, self.staff_user)
        self.assertEqual(staff_notification.actor, self.actor)
        self.assertEqual(staff_notification.data["kind"], "staff_alert")

        self.assertFalse(
            Notification.objects.filter(
                recipient=self.inactive_staff_user,
                title="Staff notification",
            ).exists()
        )

    def test_mark_user_notifications_as_read_marks_only_user_unread_notifications(self):
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
        other_user_notification = Notification.objects.create(
            recipient=self.other_user,
            title="Other unread",
            is_read=False,
        )

        updated_count = mark_user_notifications_as_read(self.user)

        self.assertEqual(updated_count, 2)

        first.refresh_from_db()
        second.refresh_from_db()
        already_read.refresh_from_db()
        other_user_notification.refresh_from_db()

        self.assertTrue(first.is_read)
        self.assertTrue(second.is_read)
        self.assertTrue(already_read.is_read)
        self.assertFalse(other_user_notification.is_read)

        self.assertIsNotNone(first.read_at)
        self.assertIsNotNone(second.read_at)
