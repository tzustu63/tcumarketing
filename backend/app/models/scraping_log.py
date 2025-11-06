"""
Scraping Log Model
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class ScrapingLog(Base):
    """
    Scraping log model for tracking scraping activities
    """
    __tablename__ = 'scraping_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    url = Column(String, nullable=False, comment="目標網址")
    action = Column(String(50), nullable=False, comment="動作類型")
    status = Column(String(20), nullable=False, comment="狀態")
    error_message = Column(String, nullable=True, comment="錯誤訊息")
    response_time = Column(Integer, nullable=True, comment="回應時間 (ms)")
    created_at = Column(DateTime, default=datetime.utcnow, comment="建立時間")
    
    # Relationships
    task = relationship("Task", back_populates="logs")
    
    def __repr__(self):
        return f"<ScrapingLog(id={self.id}, url={self.url}, status={self.status})>"
