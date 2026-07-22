# backend/config/celery.py
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('retoucher')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Schedule periodic tasks
app.conf.beat_schedule = {
    'check-project-expirations': {
        'task': 'projects.tasks.check_project_expirations',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    'check-workflow-deadlines': {
        'task': 'orders.tasks.check_workflow_deadlines',
        'schedule': crontab(minute='*/5'),
    },
    'check-proposal-deadlines': {
        'task': 'projects.tasks.check_proposal_deadlines',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
}