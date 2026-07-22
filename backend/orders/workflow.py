"""Centralized order state transitions.

This module deliberately reuses the existing ``OrderStatusHistory`` model and
keeps activity/notification creation in the existing view/service layer for
Phase 1.  Its job is to make status mutation atomic, validated and auditable.
"""
from __future__ import annotations

from collections.abc import Mapping

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Order, OrderStatusHistory


ALLOWED_ORDER_TRANSITIONS: dict[str, set[str]] = {
    Order.Status.DRAFT: {Order.Status.SUBMITTED, Order.Status.CANCELLED},
    Order.Status.SUBMITTED: {Order.Status.IN_REVIEW, Order.Status.CANCELLED},
    Order.Status.IN_REVIEW: {Order.Status.ASSIGNED, Order.Status.CANCELLED},
    Order.Status.ASSIGNED: {Order.Status.IN_PROGRESS, Order.Status.CANCELLED},
    Order.Status.IN_PROGRESS: {Order.Status.DELIVERED, Order.Status.CANCELLED},
    Order.Status.DELIVERED: {
        Order.Status.CLIENT_REVIEW,
        Order.Status.REVISION_REQUIRED,
        Order.Status.CANCELLED,
    },
    Order.Status.CLIENT_REVIEW: {
        Order.Status.CLIENT_REVISION_REQUESTED,
        Order.Status.COMPLETED,
    },
    Order.Status.CLIENT_REVISION_REQUESTED: {
        Order.Status.REVISION_REQUIRED,
        Order.Status.CLIENT_REVIEW,
    },
    Order.Status.REVISION_REQUIRED: {
        Order.Status.IN_PROGRESS,
        Order.Status.CANCELLED,
    },
    Order.Status.COMPLETED: {Order.Status.SETTLEMENT_PENDING},
    Order.Status.SETTLEMENT_PENDING: {Order.Status.PAID},
    Order.Status.PAID: {Order.Status.CLOSED},
    Order.Status.CLOSED: set(),
    Order.Status.CANCELLED: set(),
}


def _validate_extra_updates(extra_updates: Mapping[str, object]) -> None:
    protected_fields = {"id", "pk", "status", "created_at", "updated_at"}
    invalid_fields = protected_fields.intersection(extra_updates)
    if invalid_fields:
        fields = ", ".join(sorted(invalid_fields))
        raise ValidationError(f"Workflow cannot update protected fields: {fields}.")

    model_fields = {field.name for field in Order._meta.concrete_fields}
    unknown_fields = set(extra_updates).difference(model_fields)
    if unknown_fields:
        fields = ", ".join(sorted(unknown_fields))
        raise ValidationError(f"Unknown order fields: {fields}.")


@transaction.atomic
def transition_order(
    *,
    order: Order,
    to_status: str,
    actor=None,
    note: str = "",
    extra_updates: Mapping[str, object] | None = None,
    allow_same_status: bool = False,
) -> Order:
    """Move an order to another state and record ``OrderStatusHistory``.

    The row is locked before validation so two concurrent requests cannot both
    perform a transition based on a stale status.
    """
    locked_order = Order.objects.select_for_update().get(pk=order.pk)
    from_status = locked_order.status

    if to_status not in Order.Status.values:
        raise ValidationError({"status": f"Unknown order status: {to_status}."})

    if from_status == to_status:
        if allow_same_status:
            return locked_order
        raise ValidationError({"status": "Order is already in this status."})

    allowed = ALLOWED_ORDER_TRANSITIONS.get(from_status, set())
    if to_status not in allowed:
        raise ValidationError(
            {
                "status": (
                    f"Invalid order transition from '{from_status}' "
                    f"to '{to_status}'."
                )
            }
        )

    updates = dict(extra_updates or {})
    _validate_extra_updates(updates)

    for field_name, value in updates.items():
        setattr(locked_order, field_name, value)

    locked_order.status = to_status
    locked_order.save(update_fields=["status", *updates.keys(), "updated_at"])

    from .deadline_service import sync_order_deadline
    sync_order_deadline(locked_order)

    OrderStatusHistory.objects.create(
        order=locked_order,
        changed_by=actor if getattr(actor, "is_authenticated", False) else None,
        from_status=from_status,
        to_status=to_status,
        note=(note or "").strip(),
    )

    # Keep the caller's in-memory instance synchronized.
    order.status = locked_order.status
    order.updated_at = locked_order.updated_at
    for field_name in updates:
        setattr(order, field_name, getattr(locked_order, field_name))

    return locked_order


@transaction.atomic
def record_initial_order_status(
    *,
    order: Order,
    actor=None,
    note: str = "Order created.",
) -> OrderStatusHistory:
    """Create the initial history row once for an externally-created order."""
    history, _ = OrderStatusHistory.objects.get_or_create(
        order=order,
        from_status="",
        to_status=order.status,
        defaults={
            "changed_by": actor if getattr(actor, "is_authenticated", False) else None,
            "note": (note or "").strip(),
        },
    )
    return history
