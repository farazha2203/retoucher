from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Order, OrderStatusHistory
from .workflow import record_initial_order_status, transition_order


class OrderWorkflowPhase1Tests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.client_user = User.objects.create_user(
            username="phase1_client",
            password="test-pass",
            role="client",
        )
        self.editor_user = User.objects.create_user(
            username="phase1_editor",
            password="test-pass",
            role="editor",
        )
        self.order = Order.objects.create(
            client=self.client_user,
            title="Phase 1 workflow order",
        )

    def test_valid_transition_updates_order_and_creates_history(self):
        result = transition_order(
            order=self.order,
            to_status=Order.Status.SUBMITTED,
            actor=self.client_user,
            note="Submitted by client.",
        )

        self.assertEqual(result.status, Order.Status.SUBMITTED)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.SUBMITTED)

        history = OrderStatusHistory.objects.get(order=self.order)
        self.assertEqual(history.from_status, Order.Status.DRAFT)
        self.assertEqual(history.to_status, Order.Status.SUBMITTED)
        self.assertEqual(history.changed_by, self.client_user)

    def test_invalid_transition_does_not_partially_write(self):
        with self.assertRaises(ValidationError):
            transition_order(
                order=self.order,
                to_status=Order.Status.PAID,
                actor=self.client_user,
            )

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.DRAFT)
        self.assertFalse(OrderStatusHistory.objects.filter(order=self.order).exists())

    def test_extra_updates_are_saved_with_transition(self):
        self.order.status = Order.Status.IN_REVIEW
        self.order.save(update_fields=["status", "updated_at"])

        result = transition_order(
            order=self.order,
            to_status=Order.Status.ASSIGNED,
            actor=self.client_user,
            extra_updates={"editor": self.editor_user},
        )

        self.assertEqual(result.editor, self.editor_user)
        self.order.refresh_from_db()
        self.assertEqual(self.order.editor, self.editor_user)

    def test_initial_status_history_is_idempotent(self):
        record_initial_order_status(order=self.order, actor=self.client_user)
        record_initial_order_status(order=self.order, actor=self.client_user)

        self.assertEqual(self.order.status_history.count(), 1)
