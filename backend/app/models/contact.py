"""
Contact Model
"""
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Contact(Base):
    """
    Contact model for storing extracted contact information
    """
    __tablename__ = 'contacts'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    country = Column(String(2), nullable=False, default="ID", comment="國家代碼")
    keyword = Column(String(255), nullable=True, comment="搜尋關鍵字")
    institution_name = Column(String(500), nullable=False, comment="機構名稱")
    institution_type = Column(String(50), nullable=True, comment="機構類型")
    source_url = Column(String, nullable=False, comment="來源網址")
    source_platform = Column(String(20), nullable=False, comment="來源平台")
    email = Column(String(255), nullable=True, comment="Email")
    whatsapp = Column(String(50), nullable=True, comment="WhatsApp")
    additional_info = Column(JSONB, nullable=True, comment="額外資訊")
    quality_score = Column(Float, nullable=True, comment="資料品質分數")
    is_verified = Column(Boolean, default=False, comment="是否已驗證")
    extracted_at = Column(DateTime, default=datetime.utcnow, comment="萃取時間")
    
    # Relationships
    task = relationship("Task", back_populates="contacts")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('source_url', 'email', 'whatsapp', name='uix_contact_unique'),
    )
    
    def __repr__(self):
        return f"<Contact(id={self.id}, institution={self.institution_name}, email={self.email})>"
