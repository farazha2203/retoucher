# اگر tasks.py وجود ندارد، ایجاد کن:

from celery import shared_task
from .sla_handler import SLAHandler


@shared_task
def check_sla_violations():
    """Periodic task to check SLA violations."""
    late_count = SLAHandler.check_all_late_orders()
    return f"SLA check complete. Created {late_count} new penalties."

@shared_task
def check_workflow_deadlines():
    """Deadlineهای Workflow را بررسی و موارد منقضی‌شده را missed می‌کند."""
    from .deadline_service import process_overdue_deadlines

    return {
        "missed": process_overdue_deadlines(),
    }