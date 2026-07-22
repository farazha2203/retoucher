"""Read-only workflow presentation helpers for API and frontend clients.

This module does not mutate state. It converts the existing order status,
deadline, status history and activity logs into stable frontend-facing data.
"""
from __future__ import annotations

from django.utils import timezone

from .models import Order


ORDER_STAGE_DEFINITIONS = {
    Order.Status.DRAFT: ("draft", "پیش‌نویس", "Draft", 0, "client", "submit_order"),
    Order.Status.SUBMITTED: ("submission", "ثبت سفارش", "Submitted", 5, "staff", "start_review"),
    Order.Status.IN_REVIEW: ("review", "بررسی سفارش", "In review", 10, "staff", "assign_editor"),
    Order.Status.ASSIGNED: ("assignment", "تخصیص ادیتور", "Editor assigned", 20, "editor", "start_work"),
    Order.Status.IN_PROGRESS: ("editing", "در حال ادیت", "Editing", 45, "editor", "upload_delivery"),
    Order.Status.DELIVERED: ("supervisor_qc", "کنترل کیفیت ناظر", "Supervisor QC", 70, "supervisor", "review_delivery"),
    Order.Status.CLIENT_REVIEW: ("client_review", "بررسی مشتری", "Client review", 80, "client", "approve_or_request_revision"),
    Order.Status.CLIENT_REVISION_REQUESTED: ("revision_review", "بررسی درخواست اصلاح", "Revision review", 78, "supervisor", "review_revision_request"),
    Order.Status.REVISION_REQUIRED: ("revision", "در حال اصلاح", "Revision required", 65, "editor", "submit_revision"),
    Order.Status.COMPLETED: ("approved", "تأیید نهایی", "Approved", 90, "staff", "start_settlement"),
    Order.Status.SETTLEMENT_PENDING: ("settlement", "در انتظار تسویه", "Settlement pending", 95, "admin", "settle_order"),
    Order.Status.PAID: ("paid", "تسویه شده", "Paid", 99, "staff", "close_order"),
    Order.Status.CLOSED: ("closed", "بسته شده", "Closed", 100, None, None),
    Order.Status.CANCELLED: ("cancelled", "لغو شده", "Cancelled", 100, None, None),
}

TERMINAL_ORDER_STATUSES = {Order.Status.CLOSED, Order.Status.CANCELLED}
SUCCESS_ORDER_STATUSES = {Order.Status.COMPLETED, Order.Status.SETTLEMENT_PENDING, Order.Status.PAID, Order.Status.CLOSED}


def _iso(value):
    return value.isoformat() if value else None


def get_order_workflow_summary(order: Order) -> dict:
    stage_key, title_fa, title_en, percent, waiting_for_role, next_action = ORDER_STAGE_DEFINITIONS[order.status]
    now = timezone.now()
    terminal = order.status in TERMINAL_ORDER_STATUSES
    active_deadline = order.workflow_deadlines.filter(status="active").order_by("due_at").first()
    deadline = active_deadline.due_at if active_deadline else order.deadline
    overdue = bool(deadline and not terminal and deadline < now)

    if terminal:
        deadline_state = "terminal"
    elif deadline is None:
        deadline_state = "none"
    elif overdue:
        deadline_state = "overdue"
    else:
        deadline_state = "active"

    return {
        "workflow_type": "order",
        "status": order.status,
        "stage": {
            "key": stage_key,
            "title_fa": title_fa,
            "title_en": title_en,
        },
        "progress_percent": percent,
        "terminal": terminal,
        "successful": order.status in SUCCESS_ORDER_STATUSES,
        "waiting_for_role": waiting_for_role,
        "next_action": next_action,
        "deadline": {
            "at": _iso(deadline),
            "state": deadline_state,
            "is_overdue": overdue,
            "stage": active_deadline.stage if active_deadline else None,
            "owner_role": active_deadline.owner_role if active_deadline else waiting_for_role,
            "timeout_action": active_deadline.timeout_action if active_deadline else None,
        },
    }


def build_order_timeline(order: Order) -> list[dict]:
    events = []

    for item in order.status_history.select_related("changed_by").all():
        events.append({
            "event_id": f"order-status-{item.pk}",
            "event_key": "status_changed",
            "entity_type": "order",
            "entity_id": order.pk,
            "source": "status_history",
            "actor": {
                "id": item.changed_by_id,
                "username": item.changed_by.username if item.changed_by else None,
            },
            "from_status": item.from_status or None,
            "to_status": item.to_status,
            "message": item.note,
            "metadata": {},
            "occurred_at": _iso(item.created_at),
        })

    for item in order.activity_logs.select_related("actor").all():
        events.append({
            "event_id": f"order-activity-{item.pk}",
            "event_key": item.activity_type,
            "entity_type": "order",
            "entity_id": order.pk,
            "source": "activity_log",
            "actor": {
                "id": item.actor_id,
                "username": item.actor.username if item.actor else None,
            },
            "from_status": item.metadata.get("from_status"),
            "to_status": item.metadata.get("to_status"),
            "message": item.message,
            "metadata": item.metadata,
            "occurred_at": _iso(item.created_at),
        })

    events.sort(key=lambda event: (event["occurred_at"] or "", event["event_id"]), reverse=True)
    return events
