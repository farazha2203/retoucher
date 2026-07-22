"""
Celery tasks for projects app.
"""
from celery import shared_task
from .expiration_handler import ProjectExpirationHandler


@shared_task
def check_project_expirations():
    """
    Periodic task to check and expire old project requests.
    Runs every 15 minutes.
    """
    expired_count = ProjectExpirationHandler.check_and_expire_requests()
    return f"Expired {expired_count} project requests"


@shared_task
def check_proposal_deadlines():
    """
    Periodic task to auto-reject proposals past deadline.
    Runs every 15 minutes.
    """
    rejected_count = ProjectExpirationHandler.check_and_reject_proposals()
    return f"Auto-rejected {rejected_count} proposals"