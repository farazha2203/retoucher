from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from orders.deadline_service import process_overdue_deadlines
from orders.models import Order, WorkflowDeadline
from orders.workflow import transition_order

class DeadlinePhase14Tests(TestCase):
 def setUp(self):
  U=get_user_model(); self.u=U.objects.create_user(username="deadline-user",password="x")
 def test_transition_creates_and_resolves_deadlines(self):
  o=Order.objects.create(client=self.u,title="x")
  transition_order(order=o,to_status=Order.Status.SUBMITTED,actor=self.u)
  first=o.workflow_deadlines.get(status="active"); self.assertEqual(first.stage,"submission")
  transition_order(order=o,to_status=Order.Status.IN_REVIEW,actor=self.u)
  first.refresh_from_db(); self.assertEqual(first.status,"met")
  self.assertEqual(o.workflow_deadlines.get(status="active").stage,"review")
 def test_overdue_processor_is_idempotent(self):
  o=Order.objects.create(client=self.u,title="x")
  d=WorkflowDeadline.objects.create(order=o,stage="x",due_at=timezone.now()-timedelta(minutes=1))
  self.assertEqual(process_overdue_deadlines(),1); self.assertEqual(process_overdue_deadlines(),0)
  d.refresh_from_db(); self.assertEqual(d.status,"missed")
 def test_exactly_one_target_constraint(self):
  from django.db import IntegrityError, transaction
  with self.assertRaises(IntegrityError):
   with transaction.atomic(): WorkflowDeadline.objects.create(stage="x",due_at=timezone.now())
