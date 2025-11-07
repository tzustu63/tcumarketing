"""
Error Handling and Notification for Celery Tasks
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.scraping_log import ScrapingLog
from app.repositories.scraping_log_repository import ScrapingLogRepository

logger = logging.getLogger(__name__)


class TaskErrorHandler:
    """
    Centralized error handling for Celery tasks.
    Implements retry logic, error logging, and failure notifications.
    """
    
    def __init__(self, db: Session):
        """
        Initialize error handler.
        
        Args:
            db: Database session
        """
        self.db = db
        self.log_repo = ScrapingLogRepository(db)
    
    def log_error(
        self,
        task_id: str,
        url: str,
        action: str,
        error: Exception,
        retry_count: int = 0,
        max_retries: int = 3
    ) -> ScrapingLog:
        """
        Log an error to the database.
        
        Args:
            task_id: Task UUID
            url: URL where error occurred
            action: Action being performed
            error: Exception that occurred
            retry_count: Current retry attempt
            max_retries: Maximum retry attempts
            
        Returns:
            Created ScrapingLog entry
        """
        error_message = f"{type(error).__name__}: {str(error)}"
        
        if retry_count > 0:
            error_message += f" (Retry {retry_count}/{max_retries})"
        
        log_entry = {
            "task_id": task_id,
            "url": url,
            "action": action,
            "status": "error",
            "error_message": error_message,
            "response_time": 0
        }
        
        created_log = self.log_repo.create(log_entry)
        
        logger.error(
            f"Task error logged: task_id={task_id}, url={url}, "
            f"action={action}, error={error_message}"
        )
        
        return created_log
    
    def should_retry(
        self,
        error: Exception,
        retry_count: int,
        max_retries: int = 3
    ) -> bool:
        """
        Determine if a task should be retried based on error type.
        
        Args:
            error: Exception that occurred
            retry_count: Current retry count
            max_retries: Maximum retry attempts
            
        Returns:
            True if task should be retried
        """
        if retry_count >= max_retries:
            return False
        
        # Retryable error types
        retryable_errors = (
            "TimeoutException",
            "WebDriverException",
            "ConnectionError",
            "HTTPError",
            "RequestException"
        )
        
        error_type = type(error).__name__
        
        # Don't retry validation errors or not found errors
        non_retryable_errors = (
            "ValidationError",
            "ValueError",
            "KeyError",
            "NotFoundError"
        )
        
        if error_type in non_retryable_errors:
            logger.info(f"Error type {error_type} is not retryable")
            return False
        
        if error_type in retryable_errors:
            logger.info(f"Error type {error_type} is retryable")
            return True
        
        # Default: retry for unknown errors
        logger.info(f"Unknown error type {error_type}, will retry")
        return True
    
    def calculate_retry_delay(self, retry_count: int, base_delay: int = 5) -> int:
        """
        Calculate exponential backoff delay for retries.
        
        Args:
            retry_count: Current retry attempt (0-indexed)
            base_delay: Base delay in seconds
            
        Returns:
            Delay in seconds
        """
        # Exponential backoff: base_delay * (2 ^ retry_count)
        # For base_delay=5: 5s, 10s, 20s, 40s...
        delay = base_delay * (2 ** retry_count)
        
        # Cap at 5 minutes
        max_delay = 300
        return min(delay, max_delay)
    
    def notify_task_failure(
        self,
        task_id: str,
        task_name: str,
        error: Exception,
        retry_count: int
    ) -> None:
        """
        Send notification about task failure.
        
        Args:
            task_id: Task UUID
            task_name: Name of the failed task
            error: Exception that caused failure
            retry_count: Number of retries attempted
        """
        # Log the failure
        logger.error(
            f"Task failed after {retry_count} retries: "
            f"task_id={task_id}, task_name={task_name}, "
            f"error={type(error).__name__}: {str(error)}"
        )
        
        # In a production system, you would send notifications here:
        # - Email to administrators
        # - Slack/Discord webhook
        # - SMS alert
        # - Push notification to mobile app
        
        # For now, we just log it
        notification_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "task_id": task_id,
            "task_name": task_name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "retry_count": retry_count,
            "severity": "high" if retry_count >= 3 else "medium"
        }
        
        logger.warning(f"Task failure notification: {notification_data}")
    
    def get_error_statistics(self, task_id: str) -> Dict[str, Any]:
        """
        Get error statistics for a task.
        
        Args:
            task_id: Task UUID
            
        Returns:
            Dictionary with error statistics
        """
        logs = self.log_repo.get_by_task(task_id)
        
        total_logs = len(logs)
        error_logs = [log for log in logs if log.status == "error"]
        success_logs = [log for log in logs if log.status == "success"]
        
        error_count = len(error_logs)
        success_count = len(success_logs)
        
        error_rate = (error_count / total_logs * 100) if total_logs > 0 else 0
        
        # Group errors by type
        error_types = {}
        for log in error_logs:
            if log.error_message:
                error_type = log.error_message.split(":")[0]
                error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "total_operations": total_logs,
            "success_count": success_count,
            "error_count": error_count,
            "error_rate": round(error_rate, 2),
            "error_types": error_types,
            "should_alert": error_rate > 20.0  # Alert if error rate > 20%
        }
    
    def check_and_alert_high_error_rate(self, task_id: str) -> bool:
        """
        Check if error rate is high and send alert if needed.
        
        Args:
            task_id: Task UUID
            
        Returns:
            True if alert was sent
        """
        stats = self.get_error_statistics(task_id)
        
        if stats["should_alert"]:
            logger.warning(
                f"High error rate detected for task {task_id}: "
                f"{stats['error_rate']}% ({stats['error_count']}/{stats['total_operations']})"
            )
            
            # Send alert notification
            self._send_high_error_rate_alert(task_id, stats)
            return True
        
        return False
    
    def _send_high_error_rate_alert(
        self,
        task_id: str,
        stats: Dict[str, Any]
    ) -> None:
        """
        Send alert for high error rate.
        
        Args:
            task_id: Task UUID
            stats: Error statistics
        """
        alert_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "alert_type": "high_error_rate",
            "task_id": task_id,
            "error_rate": stats["error_rate"],
            "error_count": stats["error_count"],
            "total_operations": stats["total_operations"],
            "error_types": stats["error_types"],
            "severity": "critical" if stats["error_rate"] > 50 else "high"
        }
        
        logger.critical(f"High error rate alert: {alert_data}")
        
        # In production, send actual notifications here


class RetryStrategy:
    """
    Retry strategy configuration for different error types.
    """
    
    # Default retry configuration
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BASE_DELAY = 5
    
    # Error-specific retry configurations
    RETRY_CONFIG = {
        "TimeoutException": {
            "max_retries": 3,
            "base_delay": 5,
            "exponential": True
        },
        "WebDriverException": {
            "max_retries": 3,
            "base_delay": 10,
            "exponential": True
        },
        "ConnectionError": {
            "max_retries": 5,
            "base_delay": 5,
            "exponential": True
        },
        "HTTPError": {
            "max_retries": 3,
            "base_delay": 5,
            "exponential": True
        },
        "RateLimitError": {
            "max_retries": 5,
            "base_delay": 30,
            "exponential": True
        }
    }
    
    @classmethod
    def get_retry_config(cls, error: Exception) -> Dict[str, Any]:
        """
        Get retry configuration for an error type.
        
        Args:
            error: Exception instance
            
        Returns:
            Retry configuration dictionary
        """
        error_type = type(error).__name__
        
        config = cls.RETRY_CONFIG.get(error_type, {
            "max_retries": cls.DEFAULT_MAX_RETRIES,
            "base_delay": cls.DEFAULT_BASE_DELAY,
            "exponential": True
        })
        
        return config
    
    @classmethod
    def calculate_delay(
        cls,
        error: Exception,
        retry_count: int
    ) -> int:
        """
        Calculate retry delay based on error type and retry count.
        
        Args:
            error: Exception instance
            retry_count: Current retry attempt
            
        Returns:
            Delay in seconds
        """
        config = cls.get_retry_config(error)
        base_delay = config["base_delay"]
        
        if config["exponential"]:
            # Exponential backoff
            delay = base_delay * (2 ** retry_count)
        else:
            # Linear backoff
            delay = base_delay * (retry_count + 1)
        
        # Cap at 5 minutes
        return min(delay, 300)
