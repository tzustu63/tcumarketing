"""
Task Repository
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.task import Task
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """
    Repository for Task model operations
    """
    
    def __init__(self, db: Session):
        super().__init__(Task, db)
    
    def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> List[Task]:
        """Get tasks by status"""
        return (
            self.db.query(Task)
            .filter(Task.status == status)
            .order_by(desc(Task.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_pending_tasks(self) -> List[Task]:
        """Get all pending tasks"""
        return self.db.query(Task).filter(Task.status == "pending").all()
    
    def get_running_tasks(self) -> List[Task]:
        """Get all running tasks"""
        return self.db.query(Task).filter(Task.status == "running").all()
    
    def update_progress(self, task_id: str, progress: int) -> Optional[Task]:
        """Update task progress"""
        task = self.get(task_id)
        if task:
            task.progress = progress
            self.db.commit()
            self.db.refresh(task)
        return task
    
    def update_status(self, task_id: str, status: str, error_message: Optional[str] = None) -> Optional[Task]:
        """Update task status"""
        task = self.get(task_id)
        if task:
            task.status = status
            if error_message:
                task.error_message = error_message
            self.db.commit()
            self.db.refresh(task)
        return task
    
    def increment_results_count(self, task_id: str, count: int = 1) -> Optional[Task]:
        """Increment task results count"""
        task = self.get(task_id)
        if task:
            task.results_count += count
            self.db.commit()
            self.db.refresh(task)
        return task
    
    def get_recent_tasks(self, limit: int = 10) -> List[Task]:
        """Get recent tasks"""
        return (
            self.db.query(Task)
            .order_by(desc(Task.created_at))
            .limit(limit)
            .all()
        )
    
    def count_by_status(self, status: str) -> int:
        """Count tasks by status"""
        return self.db.query(Task).filter(Task.status == status).count()
