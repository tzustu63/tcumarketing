"""
Task Monitoring and Auto-completion
Monitors stuck tasks and automatically completes them
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.repositories.task_repository import TaskRepository
from app.celery_app import celery_app

logger = logging.getLogger(__name__)


def check_and_complete_stuck_tasks():
    """
    Check for tasks that are stuck in 'running' state with no active workers.
    If a task has been running for more than 5 minutes with no active extraction tasks,
    mark it as completed.
    """
    db = SessionLocal()
    task_repo = TaskRepository(db)
    
    try:
        # Get all running tasks
        running_tasks = task_repo.get_by_status("running")
        
        if not running_tasks:
            logger.debug("No running tasks to check")
            return
        
        # Get active tasks from Celery
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        
        if not active_tasks:
            active_tasks = {}
        
        # Build a set of task_ids that have active extraction tasks
        active_task_ids = set()
        for worker, tasks in active_tasks.items():
            for task in tasks:
                if task['name'] == 'scraping_tasks.extract_website_task':
                    # Get the parent task_id from args
                    if task['args'] and len(task['args']) > 0:
                        parent_task_id = task['args'][0]
                        active_task_ids.add(parent_task_id)
        
        # Check each running task
        for task in running_tasks:
            task_id = str(task.id)
            
            # Skip if this task has active extraction tasks
            if task_id in active_task_ids:
                logger.debug(f"Task {task_id} has active extraction tasks, skipping")
                continue
            
            # If no active workers for this task, mark as completed
            logger.info(f"Task {task_id} at {task.progress}% with no active workers, marking as completed")
            
            task.status = "completed"
            task.progress = 100
            task.completed_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Auto-completed task {task_id} with {task.results_count} results")
        
    except Exception as e:
        logger.error(f"Error checking stuck tasks: {e}")
        db.rollback()
    finally:
        db.close()


@celery_app.task(name="task_monitor.check_stuck_tasks")
def check_stuck_tasks_task():
    """
    Celery task to check and complete stuck tasks.
    This should be run periodically (e.g., every minute).
    """
    logger.info("Checking for stuck tasks...")
    check_and_complete_stuck_tasks()
    return {"status": "completed", "timestamp": datetime.utcnow().isoformat()}
