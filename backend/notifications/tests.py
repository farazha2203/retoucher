from django.contrib.auth import get_user_model
from django.test import TestCase

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
        self.assertEqual(notification.notification_type, Notification.Type.PROJECT_REQUEST)
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