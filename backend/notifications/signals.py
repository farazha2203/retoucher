from django.db.models.signals import post_save
from django.dispatch import receiver

from projects.models import ProjectProposal, ProjectRequestActivity

from .models import Notification
from .services import create_notification, create_notifications, notify_staff_users


def _activity_data(activity):
    metadata = activity.metadata or {}

    return {
        "activity_id": activity.id,
        "action": activity.action,
        "project_request_id": activity.project_request_id,
        **metadata,
    }


def _get_proposal_from_activity(activity):
    proposal_id = (activity.metadata or {}).get("proposal_id")

    if not proposal_id:
        return None

    return (
        ProjectProposal.objects.select_related("editor__user")
        .filter(id=proposal_id)
        .first()
    )


def _get_proposal_editor_user(activity):
    proposal = _get_proposal_from_activity(activity)

    if not proposal:
        return None

    if not proposal.editor_id:
        return None

    return proposal.editor.user


def _notify_user(
    *,
    recipient,
    activity,
    title,
    message,
    notification_type=Notification.Type.PROJECT_REQUEST,
    priority=Notification.Priority.NORMAL,
):
    if recipient is None:
        return None

    if activity.actor_id and recipient.id == activity.actor_id:
        return None

    return create_notification(
        recipient=recipient,
        actor=activity.actor,
        notification_type=notification_type,
        priority=priority,
        title=title,
        message=message,
        data=_activity_data(activity),
    )


@receiver(
    post_save,
    sender=ProjectRequestActivity,
    dispatch_uid="notifications.create_from_project_request_activity",
)
def create_notification_from_project_request_activity(sender, instance, created, **kwargs):
    if not created:
        return

    activity = instance
    project_request = activity.project_request
    action = activity.action

    if action == ProjectRequestActivity.Action.PUBLIC_PROPOSAL_SUBMITTED:
        _notify_user(
            recipient=project_request.client,
            activity=activity,
            notification_type=Notification.Type.PROPOSAL,
            title="New proposal received",
            message=f"A new proposal was submitted for {project_request.title}.",
        )
        return

    if action == ProjectRequestActivity.Action.DIRECT_PROPOSAL_SUBMITTED:
        _notify_user(
            recipient=project_request.client,
            activity=activity,
            notification_type=Notification.Type.PROPOSAL,
            title="Direct proposal received",
            message=f"Your selected editor submitted a proposal for {project_request.title}.",
        )
        return

    if action == ProjectRequestActivity.Action.DIRECT_DECLINED:
        _notify_user(
            recipient=project_request.client,
            activity=activity,
            notification_type=Notification.Type.PROPOSAL,
            priority=Notification.Priority.HIGH,
            title="Direct request declined",
            message=f"The editor declined your direct request: {project_request.title}.",
        )
        return

    if action == ProjectRequestActivity.Action.SAMPLE_PROPOSAL_SUBMITTED:
        notify_staff_users(
            actor=activity.actor,
            notification_type=Notification.Type.PROPOSAL,
            priority=Notification.Priority.HIGH,
            title="Sample proposal needs review",
            message=f"A sample proposal was submitted for {project_request.title}.",
            data=_activity_data(activity),
        )
        return

    if action == ProjectRequestActivity.Action.SAMPLE_REVIEWED:
        editor_user = _get_proposal_editor_user(activity)

        _notify_user(
            recipient=editor_user,
            activity=activity,
            notification_type=Notification.Type.PROPOSAL,
            title="Your sample was reviewed",
            message=f"Your sample proposal was reviewed for {project_request.title}.",
        )
        return

    if action == ProjectRequestActivity.Action.PROPOSAL_SELECTED:
        editor_user = _get_proposal_editor_user(activity)

        _notify_user(
            recipient=editor_user,
            activity=activity,
            notification_type=Notification.Type.PROPOSAL,
            priority=Notification.Priority.HIGH,
            title="Your proposal was selected",
            message=f"Your proposal was selected for {project_request.title}.",
        )
        return

    if action == ProjectRequestActivity.Action.MANAGED_ASSIGNED:
        editor_user = _get_proposal_editor_user(activity)

        recipients = [
            project_request.client,
            editor_user,
        ]

        recipients = [
            recipient
            for recipient in recipients
            if recipient is not None
            and not (activity.actor_id and recipient.id == activity.actor_id)
        ]

        create_notifications(
            recipients=recipients,
            actor=activity.actor,
            notification_type=Notification.Type.PROJECT_REQUEST,
            priority=Notification.Priority.HIGH,
            title="Managed project assigned",
            message=f"An editor was assigned to {project_request.title}.",
            data=_activity_data(activity),
        )
        return

    if action == ProjectRequestActivity.Action.CONVERTED_TO_ORDER:
        editor_user = _get_proposal_editor_user(activity)

        recipients = [
            project_request.client,
            editor_user,
        ]

        recipients = [
            recipient
            for recipient in recipients
            if recipient is not None
            and not (activity.actor_id and recipient.id == activity.actor_id)
        ]

        create_notifications(
            recipients=recipients,
            actor=activity.actor,
            notification_type=Notification.Type.ORDER,
            priority=Notification.Priority.HIGH,
            title="Project converted to order",
            message=f"{project_request.title} was converted to an order.",
            data=_activity_data(activity),
        )
        return