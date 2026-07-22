"""Read-only project-request workflow presentation helpers."""
from __future__ import annotations

from django.utils import timezone

from .models import ProjectRequest


PROJECT_STAGE_DEFINITIONS = {
    ProjectRequest.Status.DRAFT: ("draft", "پیش‌نویس", "Draft", 0, "client", "submit_request"),
    ProjectRequest.Status.SUBMITTED: ("submitted", "ثبت درخواست", "Submitted", 10, "staff", "review_request"),
    ProjectRequest.Status.OPEN_FOR_QUOTES: ("quotes", "دریافت پیشنهاد قیمت", "Open for quotes", 30, "editor", "submit_quote"),
    ProjectRequest.Status.OPEN_FOR_SAMPLES: ("samples", "دریافت نمونه", "Open for samples", 30, "editor", "submit_sample"),
    ProjectRequest.Status.WAITING_FOR_EDITOR: ("editor_response", "انتظار پاسخ ادیتور", "Waiting for editor", 30, "editor", "respond_to_request"),
    ProjectRequest.Status.UNDER_REVIEW: ("review", "بررسی پیشنهادها", "Under review", 50, "supervisor", "review_proposals"),
    ProjectRequest.Status.EDITOR_SELECTED: ("selection", "ادیتور انتخاب شد", "Editor selected", 75, "client", "convert_to_order"),
    ProjectRequest.Status.CONVERTED_TO_ORDER: ("converted", "تبدیل به سفارش", "Converted to order", 100, None, None),
    ProjectRequest.Status.CANCELLED: ("cancelled", "لغو شده", "Cancelled", 100, None, None),
    ProjectRequest.Status.EXPIRED: ("expired", "منقضی شده", "Expired", 100, None, None),
}

TERMINAL_PROJECT_STATUSES = {
    ProjectRequest.Status.CONVERTED_TO_ORDER,
    ProjectRequest.Status.CANCELLED,
    ProjectRequest.Status.EXPIRED,
}


def _iso(value):
    return value.isoformat() if value else None


def get_project_workflow_summary(project_request: ProjectRequest) -> dict:
    stage_key, title_fa, title_en, percent, waiting_for_role, next_action = PROJECT_STAGE_DEFINITIONS[project_request.status]
    active_deadline = project_request.workflow_deadlines.filter(status="active").order_by("due_at").first()
    deadline = active_deadline.due_at if active_deadline else (project_request.expires_at or project_request.preferred_deadline)
    terminal = project_request.status in TERMINAL_PROJECT_STATUSES
    overdue = bool(deadline and not terminal and deadline < timezone.now())

    if terminal:
        deadline_state = "terminal"
    elif deadline is None:
        deadline_state = "none"
    elif overdue:
        deadline_state = "overdue"
    else:
        deadline_state = "active"

    return {
        "workflow_type": "project_request",
        "request_type": project_request.request_type,
        "status": project_request.status,
        "stage": {
            "key": stage_key,
            "title_fa": title_fa,
            "title_en": title_en,
        },
        "progress_percent": percent,
        "terminal": terminal,
        "successful": project_request.status == ProjectRequest.Status.CONVERTED_TO_ORDER,
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


def build_project_timeline(project_request: ProjectRequest) -> list[dict]:
    events = []
    for item in project_request.activities.select_related("actor").all():
        events.append({
            "event_id": f"project-activity-{item.pk}",
            "event_key": item.action,
            "entity_type": "project_request",
            "entity_id": project_request.pk,
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
