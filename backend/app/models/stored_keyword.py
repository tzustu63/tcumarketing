"""
Stored Keyword Model
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime

from app.database import Base


class StoredKeyword(Base):
    """
    Model for storing user-defined keywords and cities
    """
    __tablename__ = 'stored_keywords'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="ID")
    country = Column(String(2), nullable=False, comment="國家代碼")
    keyword = Column(String(255), nullable=True, comment="關鍵字")
    city = Column(String(100), nullable=True, comment="城市")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="建立時間")
    is_deleted = Column(Boolean, default=False, nullable=False, comment="是否已刪除")
    
    __table_args__ = (
        {'comment': '儲存用戶自定義的關鍵字和城市'},
    )
    
    def __repr__(self):
        return f"<StoredKeyword(id={self.id}, country={self.country}, keyword={self.keyword}, city={self.city})>"




