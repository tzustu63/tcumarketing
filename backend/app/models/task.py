"""
Task Model
"""
from sqlalchemy import Column, String, Integer, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Task(Base):
    """
    Task model for storing search task information
    """
    __tablename__ = 'tasks'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keyword = Column(String(255), nullable=False, comment="搜尋關鍵字")
    city = Column(String(100), nullable=False, comment="城市")
    country = Column(String(2), nullable=False, default="ID", comment="國家代碼")
    target_platforms = Column(ARRAY(String), nullable=False, comment="目標平台")
    max_results = Column(Integer, default=100, comment="最大結果數")
    status = Column(String(20), nullable=False, default="pending", comment="任務狀態")
    progress = Column(Integer, default=0, comment="進度 (0-100)")
    results_count = Column(Integer, default=0, comment="結果數量")
    error_message = Column(String, nullable=True, comment="錯誤訊息")
    created_at = Column(DateTime, default=datetime.utcnow, comment="建立時間")
    started_at = Column(DateTime, nullable=True, comment="開始時間")
    completed_at = Column(DateTime, nullable=True, comment="完成時間")
    created_by = Column(String(100), nullable=True, comment="建立者")
    
    # Relationships
    contacts = relationship("Contact", back_populates="task", cascade="all, delete-orphan")
    logs = relationship("ScrapingLog", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Task(id={self.id}, keyword={self.keyword}, status={self.status})>"
