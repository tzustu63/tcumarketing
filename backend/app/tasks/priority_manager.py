"""
Task Queue Priority Management

Manages task priorities in Celery to ensure efficient resource allocation
and prevent overwhelming target websites.
"""
import logging
from enum import IntEnum
from typing import Optional, Dict, Any
from datetime import datetime
from celery import Task
from redis import Redis
from app.config import settings

logger = logging.getLogger(__name__)


class TaskPriority(IntEnum):
    """
    Task priority levels (lower number = higher priority).
    Celery uses 0-9 where 0 is highest priority.
    """
    CRITICAL = 0    # Critical tasks (exports, user-initiated)
    HIGH = 3        # High priority (new task initialization)
    NORMAL = 5      # Normal priority (regular scraping)
    LOW = 7         # Low priority (retry tasks, background jobs)
    BULK = 9        # Bulk operations (large exports, batch processing)


class TaskThrottleManager:
    """
    Manages task throttling to prevent overwhelming the system or target websites.
    """
    
    def __init__(self, redis_client: Optional[Redis] = None):
        """
        Initialize task throttle manager.
        
        Args:
            redis_client: Redis client for distributed throttling
        """
        self.redis_client = redis_client
        
        # Throttle limits per task type
        self.throttle_limits = {
            'scrape_google_task': {
                'max_concurrent': 2,  # Max 2 Google searches at once
                'max_per_hour': 20,   # Max 20 Google searches per hour
            },
            'extract_website_task': {
                'max_concurrent': 5,  # Max 5 website extractions at once
                'max_per_hour': 100,  # Max 100 website extractions per hour
            },
            'export_data_task': {
                'max_concurrent': 2,  # Max 2 exports at once
                'max_per_hour': 10,   # Max 10 exports per hour
            }
        }
        
        logger.info("TaskThrottleManager initialized with throttle limits")
    
    def can_execute_task(self, task_name: str) -> bool:
        """
        Check if a task can be executed based on throttle limits.
        
        Args:
            task_name: Name of the task
            
        Returns:
            True if task can execute, False otherwise
        """
        if task_name not in self.throttle_limits:
            return True  # No limits for unknown tasks
        
        limits = self.throttle_limits[task_name]
        
        # Check concurrent limit
        if not self._check_concurrent_limit(task_name, limits['max_concurrent']):
            logger.warning(
                f"Task {task_name} blocked: concurrent limit "
                f"({limits['max_concurrent']}) reached"
            )
            return False
        
        # Check hourly limit
        if not self._check_hourly_limit(task_name, limits['max_per_hour']):
            logger.warning(
                f"Task {task_name} blocked: hourly limit "
                f"({limits['max_per_hour']}) reached"
            )
            return False
        
        return True
    
    def _check_concurrent_limit(self, task_name: str, max_concurrent: int) -> bool:
        """Check if concurrent task limit is reached."""
        if not self.redis_client:
            return True  # Skip check if Redis not available
        
        try:
            key = f"throttle:concurrent:{task_name}"
            current = self.redis_client.get(key)
            current_count = int(current) if current else 0
            
            return current_count < max_concurrent
        except Exception as e:
            logger.error(f"Error checking concurrent limit: {e}")
            return True  # Allow on error
    
    def _check_hourly_limit(self, task_name: str, max_per_hour: int) -> bool:
        """Check if hourly task limit is reached."""
        if not self.redis_client:
            return True  # Skip check if Redis not available
        
        try:
            key = f"throttle:hourly:{task_name}"
            current = self.redis_client.get(key)
            current_count = int(current) if current else 0
            
            return current_count < max_per_hour
        except Exception as e:
            logger.error(f"Error checking hourly limit: {e}")
            return True  # Allow on error
    
    def record_task_start(self, task_name: str):
        """Record that a task has started."""
        if not self.redis_client or task_name not in self.throttle_limits:
            return
        
        try:
            # Increment concurrent counter
            concurrent_key = f"throttle:concurrent:{task_name}"
            self.redis_client.incr(concurrent_key)
            self.redis_client.expire(concurrent_key, 3600)  # 1 hour expiry
            
            # Increment hourly counter
            hourly_key = f"throttle:hourly:{task_name}"
            current = self.redis_client.get(hourly_key)
            if not current:
                # First task in this hour, set with 1 hour expiry
                self.redis_client.setex(hourly_key, 3600, 1)
            else:
                self.redis_client.incr(hourly_key)
            
            logger.debug(f"Recorded start for task: {task_name}")
        except Exception as e:
            logger.error(f"Error recording task start: {e}")
    
    def record_task_end(self, task_name: str):
        """Record that a task has ended."""
        if not self.redis_client or task_name not in self.throttle_limits:
            return
        
        try:
            # Decrement concurrent counter
            concurrent_key = f"throttle:concurrent:{task_name}"
            current = self.redis_client.get(concurrent_key)
            if current and int(current) > 0:
                self.redis_client.decr(concurrent_key)
            
            logger.debug(f"Recorded end for task: {task_name}")
        except Exception as e:
            logger.error(f"Error recording task end: {e}")
    
    def get_task_stats(self, task_name: str) -> Dict[str, int]:
        """Get current throttle statistics for a task."""
        if not self.redis_client:
            return {'concurrent': 0, 'hourly': 0}
        
        try:
            concurrent_key = f"throttle:concurrent:{task_name}"
            hourly_key = f"throttle:hourly:{task_name}"
            
            concurrent = self.redis_client.get(concurrent_key)
            hourly = self.redis_client.get(hourly_key)
            
            return {
                'concurrent': int(concurrent) if concurrent else 0,
                'hourly': int(hourly) if hourly else 0
            }
        except Exception as e:
            logger.error(f"Error getting task stats: {e}")
            return {'concurrent': 0, 'hourly': 0}


class PriorityTask(Task):
    """
    Base Celery task with priority and throttling support.
    """
    
    def __init__(self):
        super().__init__()
        self._throttle_manager: Optional[TaskThrottleManager] = None
    
    @property
    def throttle_manager(self) -> TaskThrottleManager:
        """Get or create throttle manager instance."""
        if self._throttle_manager is None:
            try:
                redis_client = Redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True
                )
                redis_client.ping()
                self._throttle_manager = TaskThrottleManager(redis_client)
            except Exception as e:
                logger.warning(f"Failed to connect to Redis for throttling: {e}")
                self._throttle_manager = TaskThrottleManager(None)
        
        return self._throttle_manager
    
    def before_start(self, task_id, args, kwargs):
        """Called before task execution."""
        # Check if task can execute
        if not self.throttle_manager.can_execute_task(self.name):
            logger.warning(f"Task {self.name} [{task_id}] throttled")
            # Retry with delay
            raise self.retry(countdown=30, max_retries=10)
        
        # Record task start
        self.throttle_manager.record_task_start(self.name)
        logger.info(f"Task {self.name} [{task_id}] starting")
    
    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """Called after task execution."""
        # Record task end
        self.throttle_manager.record_task_end(self.name)
        logger.info(f"Task {self.name} [{task_id}] completed with status: {status}")
    
    def apply_async(
        self,
        args=None,
        kwargs=None,
        task_id=None,
        producer=None,
        link=None,
        link_error=None,
        shadow=None,
        priority: Optional[TaskPriority] = None,
        **options
    ):
        """
        Apply task asynchronously with priority support.
        
        Args:
            priority: Task priority level
            **options: Other Celery options
        """
        # Set priority if provided
        if priority is not None:
            options['priority'] = priority.value if hasattr(priority, 'value') else priority
        elif 'priority' not in options:
            # Default priority based on task name
            default_priority = self._get_default_priority()
            options['priority'] = default_priority.value if hasattr(default_priority, 'value') else default_priority
        
        logger.debug(
            f"Queueing task {self.name} with priority {options.get('priority')}"
        )
        
        return super().apply_async(
            args=args,
            kwargs=kwargs,
            task_id=task_id,
            producer=producer,
            link=link,
            link_error=link_error,
            shadow=shadow,
            **options
        )
    
    def _get_default_priority(self) -> TaskPriority:
        """Get default priority for this task type."""
        # Map task names to priorities
        priority_map = {
            'export_data_task': TaskPriority.CRITICAL,
            'scrape_google_task': TaskPriority.HIGH,
            'extract_website_task': TaskPriority.NORMAL,
        }
        
        for task_prefix, priority in priority_map.items():
            if task_prefix in self.name:
                return priority
        
        return TaskPriority.NORMAL


def get_task_priority(task_type: str, is_retry: bool = False) -> TaskPriority:
    """
    Get appropriate priority for a task.
    
    Args:
        task_type: Type of task
        is_retry: Whether this is a retry attempt
        
    Returns:
        TaskPriority enum value
    """
    if is_retry:
        return TaskPriority.LOW
    
    priority_map = {
        'export': TaskPriority.CRITICAL,
        'google_search': TaskPriority.HIGH,
        'website_extract': TaskPriority.NORMAL,
        'social_extract': TaskPriority.NORMAL,
        'bulk': TaskPriority.BULK,
    }
    
    return priority_map.get(task_type, TaskPriority.NORMAL)


# Global throttle manager instance
_throttle_manager: Optional[TaskThrottleManager] = None


def get_throttle_manager() -> TaskThrottleManager:
    """Get or create global throttle manager instance."""
    global _throttle_manager
    
    if _throttle_manager is None:
        try:
            redis_client = Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
            redis_client.ping()
            _throttle_manager = TaskThrottleManager(redis_client)
        except Exception as e:
            logger.warning(f"Failed to connect to Redis for throttling: {e}")
            _throttle_manager = TaskThrottleManager(None)
    
    return _throttle_manager
