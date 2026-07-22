from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from .models import Order, OrderActivityLog, OrderStatusHistory
from .workflow_presentation import build_order_timeline, get_order_workflow_summary


class OrderWorkflowPresentationPhase13Tests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="client-p13", password="pass")
        self.order = Order.objects.create(
            client=self.user,
            title="Phase 1.3 order",
            status=Order.Status.IN_PROGRESS,
            deadline=timezone.now() + timedelta(hours=4),
        )

    def test_summary_contains_progress_stage_and_deadline(self):
        data = get_order_workflow_summary(self.order)
        self.assertEqual(data["progress_percent"], 45)
        self.assertEqual(data["stage"]["key"], "editing")
        self.assertEqual(data["waiting_for_role"], "editor")
        self.assertEqual(data["deadline"]["state"], "active")

    def test_timeline_normalizes_and_sorts_both_event_sources(self):
        history = OrderStatusHistory.objects.create(
            order=self.order,
            changed_by=self.user,
            from_status=Order.Status.ASSIGNED,
            to_status=Order.Status.IN_PROGRESS,
            note="Started",
        )
        activity = OrderActivityLog.objects.create(
            order=self.order,
            actor=self.user,
            activity_type=OrderActivityLog.ActivityType.WORK_STARTED,
            message="Editing started",
            metadata={"from_status": "assigned", "to_status": "in_progress"},
        )
        events = build_order_timeline(self.order)
        self.assertEqual(len(events), 2)
        self.assertEqual({event["source"] for event in events}, {"status_history", "activity_log"})
        self.assertTrue(any(event["event_id"] == f"order-status-{history.pk}" for event in events))
        self.assertTrue(any(event["event_id"] == f"order-activity-{activity.pk}" for event in events))
