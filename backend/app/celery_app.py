"""
Celery Application Configuration
"""
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Create Celery application
celery_app = Celery(
    "recruitment_tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

# Configure Celery
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    result_extended=True,
    
    # Timezone
    timezone="Asia/Jakarta",
    enable_utc=True,
    
    # Task execution
    task_track_started=True,
    task_time_limit=settings.TASK_TIMEOUT,
    task_soft_time_limit=settings.TASK_TIMEOUT - 30,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_concurrency=settings.TASK_MAX_WORKERS,
    worker_pool="prefork",
    
    # Priority configuration
    task_inherit_parent_priority=True,
    task_default_priority=5,  # Normal priority
    task_queue_max_priority=10,  # Support priorities 0-9
    
    # Retry configuration
    task_default_retry_delay=5,
    task_max_retries=3,
    
    # Result backend
    result_expires=3600,
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },
    
    # Broker configuration
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    
    # Rate limiting
    # 優化: 提高 rate limit 以加快任務執行速度
    task_annotations={
        'scraping_tasks.scrape_google_task': {
            'rate_limit': '30/m',  # 從 10/m 提高到 30/m (優化效能)
        },
        'scraping_tasks.extract_website_task': {
            'rate_limit': '60/m',  # 從 30/m 提高到 60/m (優化效能)
        },
    },
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'check-stuck-tasks-every-minute': {
        'task': 'task_monitor.check_stuck_tasks',
        'schedule': 60.0,  # Every 60 seconds
    },
}

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.tasks"])


# Task lifecycle signals
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):
    """Handler called before task execution"""
    logger.info(f"Task {task.name} [{task_id}] starting with args={args}, kwargs={kwargs}")


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **extra):
    """Handler called after task execution"""
    logger.info(f"Task {task.name} [{task_id}] completed with state={state}")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **extra):
    """Handler called on task failure"""
    logger.error(f"Task {sender.name} [{task_id}] failed with exception: {exception}")
    logger.error(f"Traceback: {traceback}")
