from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .models import Notification


def create_notification(
    *,
    recipient,
    title,
    message="",
    actor=None,
    notification_type=Notification.Type.SYSTEM,
    priority=Notification.Priority.NORMAL,
    data=None,
):
    if recipient is None:
        return None

    return Notification.objects.create(
        recipient=recipient,
        actor=actor,
        notification_type=notification_type,
        priority=priority,
        title=title,
        message=message,
        data=data or {},
    )


def create_notifications(
    *,
    recipients,
    title,
    message="",
    actor=None,
    notification_type=Notification.Type.SYSTEM,
    priority=Notification.Priority.NORMAL,
    data=None,
):
    unique_recipients = []
    seen_ids = set()

    for recipient in recipients:
        if recipient is None:
            continue

        if recipient.id in seen_ids:
            continue

        seen_ids.add(recipient.id)
        unique_recipients.append(recipient)

    notifications = [
        Notification(
            recipient=recipient,
            actor=actor,
            notification_type=notification_type,
            priority=priority,
            title=title,
            message=message,
            data=data or {},
        )
        for recipient in unique_recipients
    ]

    if not notifications:
        return []

    return Notification.objects.bulk_create(notifications)


def notify_staff_users(
    *,
    title,
    message="",
    actor=None,
    notification_type=Notification.Type.SYSTEM,
    priority=Notification.Priority.NORMAL,
    data=None,
):
    User = get_user_model()

    staff_users = User.objects.filter(
        is_staff=True,
        is_active=True,
    )

    return create_notifications(
        recipients=staff_users,
        title=title,
        message=message,
        actor=actor,
        notification_type=notification_type,
        priority=priority,
        data=data,
    )


@transaction.atomic
def mark_user_notifications_as_read(user):
    now = timezone.now()

    updated_count = Notification.objects.filter(
        recipient=user,
        is_read=False,
    ).update(
        is_read=True,
        read_at=now,
    )

    return updated_count