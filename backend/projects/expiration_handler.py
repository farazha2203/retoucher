"""
Expiration and deadline enforcement for projects and proposals.
"""
from datetime import timedelta
from django.utils import timezone
from .models import ProjectRequest, ProjectProposal, ProjectRequestActivity
from .workflow import transition_project_request
from notifications.models import Notification
from notifications.services import create_notification
from django.contrib.auth import get_user_model

User = get_user_model()


class ProjectExpirationHandler:
    REQUEST_EXPIRATION_DAYS = {
        ProjectRequest.RequestType.DIRECT_EDITOR: 7,
        ProjectRequest.RequestType.PUBLIC_QUOTE: 14,
        ProjectRequest.RequestType.SAMPLE_CHALLENGE: 14,
        ProjectRequest.RequestType.MANAGED_ORDER: 3,
    }

    PROPOSAL_RESPONSE_HOURS = {
        ProjectRequest.RequestType.PUBLIC_QUOTE: 72,
        ProjectRequest.RequestType.SAMPLE_CHALLENGE: 120,
    }

    @staticmethod
    def get_expiration_date(project_request):
        if not project_request.submitted_at:
            return None
        days = ProjectExpirationHandler.REQUEST_EXPIRATION_DAYS.get(
            project_request.request_type
        )
        if days is None:
            return None
        return project_request.submitted_at + timedelta(days=days)

    @staticmethod
    def check_and_expire_requests():
        now = timezone.now()
        expired_count = 0
        
        active_statuses = [
            ProjectRequest.Status.SUBMITTED,
            ProjectRequest.Status.OPEN_FOR_QUOTES,
            ProjectRequest.Status.OPEN_FOR_SAMPLES,
            ProjectRequest.Status.WAITING_FOR_EDITOR,
            ProjectRequest.Status.UNDER_REVIEW,
        ]
        
        requests_to_check = ProjectRequest.objects.filter(
            status__in=active_statuses,
            submitted_at__isnull=False,
        ).select_related('client')

        for project_request in requests_to_check:
            expiration_date = ProjectExpirationHandler.get_expiration_date(
                project_request
            )
            
            if expiration_date and now > expiration_date:
                old_status = project_request.status
                transition_project_request(
                    project_request=project_request,
                    to_status=ProjectRequest.Status.EXPIRED,
                    actor=None,
                    action=ProjectRequestActivity.Action.EXPIRED,
                    message=f"Project request expired automatically (was {old_status}).",
                    metadata={
                        "old_status": old_status,
                        "expiration_date": expiration_date.isoformat(),
                    },
                )
                expired_count += 1

                try:
                    create_notification(
                        recipient=project_request.client,
                        notification_type=Notification.Type.PROJECT_REQUEST,  # ✅ FIXED
                        title="Project request expired",
                        message=f"Your project request '{project_request.title}' has expired.",
                        data={
                            'project_request_id': project_request.id,
                            'action': ProjectRequestActivity.Action.EXPIRED,
                        },
                    )
                except Exception as e:
                    print(f"Error creating notification: {e}")

        return expired_count

    @staticmethod
    def check_and_reject_proposals():
        now = timezone.now()
        rejected_count = 0

        under_review_proposals = ProjectProposal.objects.filter(
            status=ProjectProposal.Status.UNDER_REVIEW,
            submitted_at__isnull=False,
        ).select_related('project_request', 'editor', 'editor__user')

        for proposal in under_review_proposals:
            request_type = proposal.project_request.request_type
            
            if request_type not in [
                ProjectRequest.RequestType.PUBLIC_QUOTE,
                ProjectRequest.RequestType.SAMPLE_CHALLENGE,
            ]:
                continue

            hours_limit = ProjectExpirationHandler.PROPOSAL_RESPONSE_HOURS.get(
                request_type
            )
            
            if not hours_limit:
                continue

            deadline = proposal.submitted_at + timedelta(hours=hours_limit)
            
            if now > deadline:
                old_status = proposal.status
                proposal.status = ProjectProposal.Status.REJECTED_BY_SUPERVISOR
                proposal.save(update_fields=['status', 'updated_at'])
                rejected_count += 1

                ProjectRequestActivity.objects.create(
                    project_request=proposal.project_request,
                    actor=None,
                    action=ProjectRequestActivity.Action.PROPOSAL_AUTO_REJECTED,
                    message=f"Proposal auto-rejected due to review deadline.",
                    metadata={
                        'proposal_id': proposal.id,
                        'hours_limit': hours_limit,
                    },
                )

                try:
                    create_notification(
                        recipient=proposal.editor.user,
                        notification_type=Notification.Type.PROPOSAL,  # ✅ FIXED
                        title="Your proposal was not reviewed in time",
                        message=f"Your proposal for '{proposal.project_request.title}' was automatically rejected.",
                        priority=Notification.Priority.HIGH,
                        data={
                            'project_request_id': proposal.project_request.id,
                            'proposal_id': proposal.id,
                        },
                    )
                except Exception as e:
                    print(f"Error creating notification: {e}")

        return rejected_count


class ProposalDeadlineHandler:
    @staticmethod
    def get_proposal_deadline(proposal):
        hours = ProjectExpirationHandler.PROPOSAL_RESPONSE_HOURS.get(
            proposal.project_request.request_type
        )
        if hours is None:
            return None
        return proposal.submitted_at + timedelta(hours=hours)

    @staticmethod
    def get_remaining_hours(proposal):
        deadline = ProposalDeadlineHandler.get_proposal_deadline(proposal)
        if deadline is None:
            return None
        remaining = (deadline - timezone.now()).total_seconds() / 3600
        return int(remaining)


def run_expiration_checks():
    import logging
    logger = logging.getLogger(__name__)

    try:
        expired_requests = ProjectExpirationHandler.check_and_expire_requests()
        logger.info(f"Expired {expired_requests} project requests")
    except Exception as e:
        logger.error(f"Error in check_and_expire_requests: {e}")

    try:
        rejected_proposals = ProjectExpirationHandler.check_and_reject_proposals()
        logger.info(f"Auto-rejected {rejected_proposals} proposals")
    except Exception as e:
        logger.error(f"Error in check_and_reject_proposals: {e}")