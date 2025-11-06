"""
Data Access Layer - Repository Pattern
"""
from app.repositories.base import BaseRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.contact_repository import ContactRepository
from app.repositories.scraping_log_repository import ScrapingLogRepository

__all__ = [
    "BaseRepository",
    "TaskRepository",
    "ContactRepository",
    "ScrapingLogRepository",
]
