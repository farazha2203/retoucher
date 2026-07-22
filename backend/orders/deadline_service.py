from __future__ import annotations

from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from .models import Order, WorkflowDeadline

ORDER_DEADLINE_POLICY = {
    Order.Status.SUBMITTED: ("submission", "staff", 2, "escalate_to_admin"),
    Order.Status.IN_REVIEW: ("review", "staff", 4, "escalate_to_admin"),
    Order.Status.ASSIGNED: ("assignment", "editor", 4, "notify"),
    Order.Status.IN_PROGRESS: ("editing", "editor", 48, "escalate_to_supervisor"),
    Order.Status.DELIVERED: ("supervisor_qc", "supervisor", 12, "escalate_to_admin"),
    Order.Status.CLIENT_REVIEW: ("client_review", "client", 72, "auto_approve"),
    Order.Status.CLIENT_REVISION_REQUESTED: ("revision_review", "supervisor", 12, "escalate_to_admin"),
    Order.Status.REVISION_REQUIRED: ("revision", "editor", 24, "auto_reassign"),
    Order.Status.COMPLETED: ("approved", "staff", 4, "start_settlement"),
    Order.Status.SETTLEMENT_PENDING: ("settlement", "admin", 24, "escalate_to_admin"),
    Order.Status.PAID: ("paid", "staff", 4, "close_order"),
}

PROJECT_DEADLINE_POLICY = {
    "submitted": ("submitted", "staff", 4, "escalate_to_admin"),
    "open_for_quotes": ("quotes", "editor", 72, "expire_project"),
    "open_for_samples": ("samples", "editor", 72, "expire_project"),
    "waiting_for_editor": ("editor_response", "editor", 24, "expire_project"),
    "under_review": ("review", "supervisor", 24, "escalate_to_admin"),
    "editor_selected": ("selection", "client", 24, "notify"),
}

def _resolve_active(*, order=None, project_request=None, status=WorkflowDeadline.Status.MET):
    now = timezone.now()
    qs = WorkflowDeadline.objects.select_for_update().filter(status=WorkflowDeadline.Status.ACTIVE)
    qs = qs.filter(order=order) if order is not None else qs.filter(project_request=project_request)
    updates={"status": status, "updated_at": now}
    if status == WorkflowDeadline.Status.MET: updates["met_at"] = now
    elif status == WorkflowDeadline.Status.CANCELLED: updates["cancelled_at"] = now
    return qs.update(**updates)

def _create(*, order=None, project_request=None, policy=None, due_at=None):
    if not policy: return None
    stage, owner_role, hours, timeout_action = policy
    return WorkflowDeadline.objects.create(
        order=order, project_request=project_request, stage=stage, owner_role=owner_role,
        due_at=due_at or timezone.now()+timedelta(hours=hours), timeout_action=timeout_action,
        metadata={"policy_hours": hours},
    )

@transaction.atomic
def sync_order_deadline(order):
    _resolve_active(order=order)
    return _create(order=order, policy=ORDER_DEADLINE_POLICY.get(order.status), due_at=order.deadline if order.status==Order.Status.IN_PROGRESS and order.deadline else None)

@transaction.atomic
def sync_project_deadline(project_request):
    _resolve_active(project_request=project_request)
    due = project_request.expires_at if project_request.status in {"open_for_quotes","open_for_samples","waiting_for_editor"} else None
    return _create(project_request=project_request, policy=PROJECT_DEADLINE_POLICY.get(project_request.status), due_at=due)

@transaction.atomic
def process_overdue_deadlines(now=None):
    now = now or timezone.now()
    qs = WorkflowDeadline.objects.select_for_update().filter(status=WorkflowDeadline.Status.ACTIVE, due_at__lt=now)
    count=0
    for item in qs:
        grace_deadline=item.due_at+timedelta(minutes=item.grace_period_minutes)
        if grace_deadline > now: continue
        item.status=WorkflowDeadline.Status.MISSED
        item.missed_at=now
        item.save(update_fields=["status","missed_at","updated_at"]); count+=1
    return count
