"""
Scraping Log Repository
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from app.models.scraping_log import ScrapingLog
from app.repositories.base import BaseRepository


class ScrapingLogRepository(BaseRepository[ScrapingLog]):
    """
    Repository for ScrapingLog model operations
    """
    
    def __init__(self, db: Session):
        super().__init__(ScrapingLog, db)
    
    def get_by_task(self, task_id: str, skip: int = 0, limit: int = 100) -> List[ScrapingLog]:
        """Get logs by task ID"""
        return (
            self.db.query(ScrapingLog)
            .filter(ScrapingLog.task_id == task_id)
            .order_by(desc(ScrapingLog.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[ScrapingLog]:
        """Get logs by status"""
        return (
            self.db.query(ScrapingLog)
            .filter(ScrapingLog.status == status)
            .order_by(desc(ScrapingLog.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_errors(self, task_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[ScrapingLog]:
        """Get error logs"""
        query = self.db.query(ScrapingLog).filter(ScrapingLog.status == "error")
        
        if task_id:
            query = query.filter(ScrapingLog.task_id == task_id)
        
        return (
            query
            .order_by(desc(ScrapingLog.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_recent_logs(self, hours: int = 24, limit: int = 100) -> List[ScrapingLog]:
        """Get recent logs within specified hours"""
        since = datetime.utcnow() - timedelta(hours=hours)
        return (
            self.db.query(ScrapingLog)
            .filter(ScrapingLog.created_at >= since)
            .order_by(desc(ScrapingLog.created_at))
            .limit(limit)
            .all()
        )
    
    def count_by_status(self, task_id: Optional[str] = None) -> dict:
        """Count logs by status"""
        query = self.db.query(ScrapingLog.status, func.count(ScrapingLog.id))
        
        if task_id:
            query = query.filter(ScrapingLog.task_id == task_id)
        
        results = query.group_by(ScrapingLog.status).all()
        return {status: count for status, count in results}
    
    def calculate_error_rate(self, task_id: Optional[str] = None) -> float:
        """Calculate error rate"""
        status_counts = self.count_by_status(task_id)
        total = sum(status_counts.values())
        errors = status_counts.get("error", 0)
        
        if total == 0:
            return 0.0
        
        return (errors / total) * 100
    
    def get_average_response_time(self, task_id: Optional[str] = None) -> Optional[float]:
        """Get average response time"""
        query = self.db.query(func.avg(ScrapingLog.response_time))
        
        if task_id:
            query = query.filter(ScrapingLog.task_id == task_id)
        
        result = query.scalar()
        return float(result) if result else None
    
    def cleanup_old_logs(self, days: int = 30) -> int:
        """Delete logs older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted = (
            self.db.query(ScrapingLog)
            .filter(ScrapingLog.created_at < cutoff_date)
            .delete()
        )
        self.db.commit()
        return deleted
