"""Centralized state transitions for project requests."""
from __future__ import annotations

from collections.abc import Mapping

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import ProjectRequest, ProjectRequestActivity


ALLOWED_PROJECT_TRANSITIONS: dict[str, set[str]] = {
    ProjectRequest.Status.DRAFT: {
        ProjectRequest.Status.SUBMITTED,
        ProjectRequest.Status.OPEN_FOR_QUOTES,
        ProjectRequest.Status.OPEN_FOR_SAMPLES,
        ProjectRequest.Status.WAITING_FOR_EDITOR,
        ProjectRequest.Status.CANCELLED,
    },
    ProjectRequest.Status.SUBMITTED: {
        ProjectRequest.Status.UNDER_REVIEW,
        ProjectRequest.Status.EDITOR_SELECTED,
        ProjectRequest.Status.CANCELLED,
        ProjectRequest.Status.EXPIRED,
    },
    ProjectRequest.Status.OPEN_FOR_QUOTES: {
        ProjectRequest.Status.EDITOR_SELECTED,
        ProjectRequest.Status.CANCELLED,
        ProjectRequest.Status.EXPIRED,
    },
    ProjectRequest.Status.OPEN_FOR_SAMPLES: {
        ProjectRequest.Status.UNDER_REVIEW,
        ProjectRequest.Status.EDITOR_SELECTED,
        ProjectRequest.Status.CANCELLED,
        ProjectRequest.Status.EXPIRED,
    },
    ProjectRequest.Status.WAITING_FOR_EDITOR: {
        ProjectRequest.Status.EDITOR_SELECTED,
        ProjectRequest.Status.CANCELLED,
        ProjectRequest.Status.EXPIRED,
    },
    ProjectRequest.Status.UNDER_REVIEW: {
        ProjectRequest.Status.EDITOR_SELECTED,
        ProjectRequest.Status.CANCELLED,
        ProjectRequest.Status.EXPIRED,
    },
    ProjectRequest.Status.EDITOR_SELECTED: {
        ProjectRequest.Status.CONVERTED_TO_ORDER,
        ProjectRequest.Status.CANCELLED,
    },
    ProjectRequest.Status.CONVERTED_TO_ORDER: set(),
    ProjectRequest.Status.CANCELLED: set(),
    ProjectRequest.Status.EXPIRED: set(),
}


def _validate_extra_updates(extra_updates: Mapping[str, object]) -> None:
    protected_fields = {"id", "pk", "status", "created_at", "updated_at"}
    invalid_fields = protected_fields.intersection(extra_updates)
    if invalid_fields:
        fields = ", ".join(sorted(invalid_fields))
        raise ValidationError(f"Workflow cannot update protected fields: {fields}.")

    model_fields = {field.name for field in ProjectRequest._meta.concrete_fields}
    unknown_fields = set(extra_updates).difference(model_fields)
    if unknown_fields:
        fields = ", ".join(sorted(unknown_fields))
        raise ValidationError(f"Unknown project request fields: {fields}.")


@transaction.atomic
def transition_project_request(
    *,
    project_request: ProjectRequest,
    to_status: str,
    actor=None,
    action: str | None = None,
    message: str = "",
    metadata: Mapping[str, object] | None = None,
    extra_updates: Mapping[str, object] | None = None,
    allow_same_status: bool = False,
) -> ProjectRequest:
    """Atomically mutate a project request and optionally append an activity."""
    locked_request = ProjectRequest.objects.select_for_update().get(
        pk=project_request.pk
    )
    from_status = locked_request.status

    if to_status not in ProjectRequest.Status.values:
        raise ValidationError({"status": f"Unknown project status: {to_status}."})

    if from_status == to_status:
        if allow_same_status:
            return locked_request
        raise ValidationError({"status": "Project request is already in this status."})

    allowed = ALLOWED_PROJECT_TRANSITIONS.get(from_status, set())
    if to_status not in allowed:
        raise ValidationError(
            {
                "status": (
                    f"Invalid project transition from '{from_status}' "
                    f"to '{to_status}'."
                )
            }
        )

    updates = dict(extra_updates or {})
    _validate_extra_updates(updates)

    for field_name, value in updates.items():
        setattr(locked_request, field_name, value)

    locked_request.status = to_status
    locked_request.save(update_fields=["status", *updates.keys(), "updated_at"])

    from orders.deadline_service import sync_project_deadline
    sync_project_deadline(locked_request)

    if action is not None:
        event_metadata = dict(metadata or {})
        event_metadata.setdefault("from_status", from_status)
        event_metadata.setdefault("to_status", to_status)
        ProjectRequestActivity.objects.create(
            project_request=locked_request,
            actor=actor if getattr(actor, "is_authenticated", False) else None,
            action=action,
            message=(message or "").strip(),
            metadata=event_metadata,
        )

    project_request.status = locked_request.status
    project_request.updated_at = locked_request.updated_at
    for field_name in updates:
        setattr(project_request, field_name, getattr(locked_request, field_name))

    return locked_request
