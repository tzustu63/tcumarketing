"""
Monitoring and metrics calculation.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.task import Task
from app.models.scraping_log import ScrapingLog
from app.models.contact import Contact
from app.logging_config import get_logger

logger = get_logger(__name__)


class MetricsCalculator:
    """Calculate system metrics and statistics."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_task_success_rate(
        self,
        task_id: Optional[str] = None,
        time_window_hours: Optional[int] = None
    ) -> float:
        """
        Calculate task success rate.
        
        Args:
            task_id: Optional specific task ID
            time_window_hours: Optional time window in hours
        
        Returns:
            Success rate as a percentage (0-100)
        """
        try:
            query = self.db.query(Task)
            
            if task_id:
                query = query.filter(Task.id == task_id)
            
            if time_window_hours:
                cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
                query = query.filter(Task.created_at >= cutoff_time)
            
            # Only consider completed or failed tasks
            query = query.filter(Task.status.in_(['completed', 'failed']))
            
            total_tasks = query.count()
            
            if total_tasks == 0:
                return 100.0  # No tasks means 100% success rate
            
            successful_tasks = query.filter(Task.status == 'completed').count()
            
            success_rate = (successful_tasks / total_tasks) * 100
            return round(success_rate, 2)
        
        except Exception as e:
            logger.error(f"Error calculating task success rate: {e}")
            return 0.0
    
    def calculate_error_rate(
        self,
        task_id: Optional[str] = None,
        time_window_hours: Optional[int] = None
    ) -> float:
        """
        Calculate error rate from scraping logs.
        
        Args:
            task_id: Optional specific task ID
            time_window_hours: Optional time window in hours
        
        Returns:
            Error rate as a percentage (0-100)
        """
        try:
            query = self.db.query(ScrapingLog)
            
            if task_id:
                query = query.filter(ScrapingLog.task_id == task_id)
            
            if time_window_hours:
                cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
                query = query.filter(ScrapingLog.created_at >= cutoff_time)
            
            total_logs = query.count()
            
            if total_logs == 0:
                return 0.0  # No logs means 0% error rate
            
            error_logs = query.filter(ScrapingLog.status == 'error').count()
            
            error_rate = (error_logs / total_logs) * 100
            return round(error_rate, 2)
        
        except Exception as e:
            logger.error(f"Error calculating error rate: {e}")
            return 0.0
    
    def get_task_statistics(
        self,
        task_id: Optional[str] = None,
        time_window_hours: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive task statistics.
        
        Args:
            task_id: Optional specific task ID
            time_window_hours: Optional time window in hours
        
        Returns:
            Dictionary containing various statistics
        """
        try:
            task_query = self.db.query(Task)
            
            if task_id:
                task_query = task_query.filter(Task.id == task_id)
            
            if time_window_hours:
                cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
                task_query = task_query.filter(Task.created_at >= cutoff_time)
            
            # Task counts by status
            total_tasks = task_query.count()
            pending_tasks = task_query.filter(Task.status == 'pending').count()
            running_tasks = task_query.filter(Task.status == 'running').count()
            completed_tasks = task_query.filter(Task.status == 'completed').count()
            failed_tasks = task_query.filter(Task.status == 'failed').count()
            
            # Contact statistics
            contact_query = self.db.query(Contact)
            if task_id:
                contact_query = contact_query.filter(Contact.task_id == task_id)
            if time_window_hours:
                cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
                contact_query = contact_query.filter(Contact.extracted_at >= cutoff_time)
            
            total_contacts = contact_query.count()
            contacts_with_email = contact_query.filter(Contact.email.isnot(None)).count()
            contacts_with_whatsapp = contact_query.filter(Contact.whatsapp.isnot(None)).count()
            
            # Average quality score
            avg_quality_score = self.db.query(func.avg(Contact.quality_score)).scalar() or 0.0
            
            # Success and error rates
            success_rate = self.calculate_task_success_rate(task_id, time_window_hours)
            error_rate = self.calculate_error_rate(task_id, time_window_hours)
            
            return {
                "tasks": {
                    "total": total_tasks,
                    "pending": pending_tasks,
                    "running": running_tasks,
                    "completed": completed_tasks,
                    "failed": failed_tasks,
                    "success_rate": success_rate
                },
                "contacts": {
                    "total": total_contacts,
                    "with_email": contacts_with_email,
                    "with_whatsapp": contacts_with_whatsapp,
                    "avg_quality_score": round(avg_quality_score, 2)
                },
                "errors": {
                    "error_rate": error_rate
                }
            }
        
        except Exception as e:
            logger.error(f"Error getting task statistics: {e}")
            return {
                "tasks": {"total": 0, "pending": 0, "running": 0, "completed": 0, "failed": 0, "success_rate": 0.0},
                "contacts": {"total": 0, "with_email": 0, "with_whatsapp": 0, "avg_quality_score": 0.0},
                "errors": {"error_rate": 0.0}
            }
    
    def get_recent_errors(
        self,
        limit: int = 10,
        task_id: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        """
        Get recent error logs.
        
        Args:
            limit: Maximum number of errors to return
            task_id: Optional specific task ID
        
        Returns:
            List of error log dictionaries
        """
        try:
            query = self.db.query(ScrapingLog).filter(ScrapingLog.status == 'error')
            
            if task_id:
                query = query.filter(ScrapingLog.task_id == task_id)
            
            query = query.order_by(ScrapingLog.created_at.desc()).limit(limit)
            
            errors = []
            for log in query.all():
                errors.append({
                    "id": str(log.id),
                    "task_id": str(log.task_id) if log.task_id else None,
                    "url": log.url,
                    "action": log.action,
                    "error_message": log.error_message,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                })
            
            return errors
        
        except Exception as e:
            logger.error(f"Error getting recent errors: {e}")
            return []


class AlertManager:
    """Manage alerts and notifications."""
    
    def __init__(self, db: Session):
        self.db = db
        self.metrics_calculator = MetricsCalculator(db)
    
    def check_error_rate_threshold(
        self,
        task_id: Optional[str] = None,
        threshold: float = 20.0,
        time_window_hours: int = 1
    ) -> Dict[str, Any]:
        """
        Check if error rate exceeds threshold.
        
        Args:
            task_id: Optional specific task ID
            threshold: Error rate threshold percentage (default 20%)
            time_window_hours: Time window to check (default 1 hour)
        
        Returns:
            Dictionary with alert status and details
        """
        try:
            error_rate = self.metrics_calculator.calculate_error_rate(
                task_id=task_id,
                time_window_hours=time_window_hours
            )
            
            alert_triggered = error_rate > threshold
            
            if alert_triggered:
                logger.warning(
                    f"Error rate alert triggered: {error_rate}% exceeds threshold {threshold}%",
                    extra={"task_id": task_id, "error_rate": error_rate, "threshold": threshold}
                )
            
            return {
                "alert_triggered": alert_triggered,
                "error_rate": error_rate,
                "threshold": threshold,
                "time_window_hours": time_window_hours,
                "task_id": task_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error checking error rate threshold: {e}")
            return {
                "alert_triggered": False,
                "error": str(e)
            }
    
    def check_task_failure_rate(
        self,
        threshold: float = 50.0,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Check if task failure rate exceeds threshold.
        
        Args:
            threshold: Failure rate threshold percentage (default 50%)
            time_window_hours: Time window to check (default 24 hours)
        
        Returns:
            Dictionary with alert status and details
        """
        try:
            success_rate = self.metrics_calculator.calculate_task_success_rate(
                time_window_hours=time_window_hours
            )
            
            failure_rate = 100.0 - success_rate
            alert_triggered = failure_rate > threshold
            
            if alert_triggered:
                logger.warning(
                    f"Task failure rate alert triggered: {failure_rate}% exceeds threshold {threshold}%",
                    extra={"failure_rate": failure_rate, "threshold": threshold}
                )
            
            return {
                "alert_triggered": alert_triggered,
                "failure_rate": failure_rate,
                "success_rate": success_rate,
                "threshold": threshold,
                "time_window_hours": time_window_hours,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error checking task failure rate: {e}")
            return {
                "alert_triggered": False,
                "error": str(e)
            }
    
    def get_all_alerts(
        self,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check all alert conditions and return status.
        
        Args:
            task_id: Optional specific task ID
        
        Returns:
            Dictionary with all alert statuses
        """
        try:
            error_rate_alert = self.check_error_rate_threshold(task_id=task_id)
            task_failure_alert = self.check_task_failure_rate()
            
            any_alert_triggered = (
                error_rate_alert.get("alert_triggered", False) or
                task_failure_alert.get("alert_triggered", False)
            )
            
            return {
                "any_alert_triggered": any_alert_triggered,
                "alerts": {
                    "error_rate": error_rate_alert,
                    "task_failure": task_failure_alert
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error getting all alerts: {e}")
            return {
                "any_alert_triggered": False,
                "error": str(e)
            }
