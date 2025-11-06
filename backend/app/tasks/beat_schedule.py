"""
Celery Beat Schedule Configuration
Defines periodic tasks
"""
from celery.schedules import crontab

# Celery Beat schedule
beat_schedule = {
    'check-stuck-tasks-every-minute': {
        'task': 'task_monitor.check_stuck_tasks',
        'schedule': 60.0,  # Every 60 seconds
    },
}
