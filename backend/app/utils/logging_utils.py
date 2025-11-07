"""
Utility functions for logging scraping activities to the database.
"""

from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.scraping_log import ScrapingLog
from app.logging_config import get_logger

logger = get_logger(__name__)


def log_scraping_to_db(
    db: Session,
    task_id: Optional[str],
    url: str,
    action: str,
    status: str,
    error_message: Optional[str] = None,
    response_time: Optional[int] = None
) -> Optional[ScrapingLog]:
    """
    Log scraping activity to the database.
    
    Args:
        db: Database session
        task_id: Task ID
        url: URL being scraped
        action: Action being performed (e.g., 'google_search', 'fetch_page', 'extract_contact')
        status: Status of the action ('success', 'error', 'warning')
        error_message: Optional error message
        response_time: Optional response time in milliseconds
    
    Returns:
        Created ScrapingLog instance or None if failed
    """
    try:
        log_entry = ScrapingLog(
            task_id=task_id,
            url=url,
            action=action,
            status=status,
            error_message=error_message,
            response_time=response_time,
            created_at=datetime.utcnow()
        )
        
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        
        return log_entry
    except Exception as e:
        logger.error(f"Failed to log scraping activity to database: {e}")
        db.rollback()
        return None


def log_scraping_success(
    db: Session,
    task_id: Optional[str],
    url: str,
    action: str,
    response_time: Optional[int] = None
) -> Optional[ScrapingLog]:
    """
    Log successful scraping activity.
    
    Args:
        db: Database session
        task_id: Task ID
        url: URL being scraped
        action: Action being performed
        response_time: Optional response time in milliseconds
    
    Returns:
        Created ScrapingLog instance or None if failed
    """
    return log_scraping_to_db(
        db=db,
        task_id=task_id,
        url=url,
        action=action,
        status='success',
        response_time=response_time
    )


def log_scraping_error(
    db: Session,
    task_id: Optional[str],
    url: str,
    action: str,
    error_message: str,
    response_time: Optional[int] = None
) -> Optional[ScrapingLog]:
    """
    Log scraping error.
    
    Args:
        db: Database session
        task_id: Task ID
        url: URL being scraped
        action: Action being performed
        error_message: Error message
        response_time: Optional response time in milliseconds
    
    Returns:
        Created ScrapingLog instance or None if failed
    """
    return log_scraping_to_db(
        db=db,
        task_id=task_id,
        url=url,
        action=action,
        status='error',
        error_message=error_message,
        response_time=response_time
    )


def get_error_logs(
    db: Session,
    task_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> list[ScrapingLog]:
    """
    Get error logs from the database.
    
    Args:
        db: Database session
        task_id: Optional task ID to filter by
        limit: Maximum number of logs to return
        offset: Number of logs to skip
    
    Returns:
        List of ScrapingLog instances
    """
    query = db.query(ScrapingLog).filter(ScrapingLog.status == 'error')
    
    if task_id:
        query = query.filter(ScrapingLog.task_id == task_id)
    
    query = query.order_by(ScrapingLog.created_at.desc())
    query = query.limit(limit).offset(offset)
    
    return query.all()


def get_task_logs(
    db: Session,
    task_id: str,
    limit: int = 100,
    offset: int = 0
) -> list[ScrapingLog]:
    """
    Get all logs for a specific task.
    
    Args:
        db: Database session
        task_id: Task ID
        limit: Maximum number of logs to return
        offset: Number of logs to skip
    
    Returns:
        List of ScrapingLog instances
    """
    query = db.query(ScrapingLog).filter(ScrapingLog.task_id == task_id)
    query = query.order_by(ScrapingLog.created_at.desc())
    query = query.limit(limit).offset(offset)
    
    return query.all()


def count_error_logs(
    db: Session,
    task_id: Optional[str] = None
) -> int:
    """
    Count error logs.
    
    Args:
        db: Database session
        task_id: Optional task ID to filter by
    
    Returns:
        Number of error logs
    """
    query = db.query(ScrapingLog).filter(ScrapingLog.status == 'error')
    
    if task_id:
        query = query.filter(ScrapingLog.task_id == task_id)
    
    return query.count()
