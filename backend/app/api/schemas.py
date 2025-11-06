"""
API Schemas (Pydantic Models)
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# ============================================================================
# Task Schemas
# ============================================================================

class TaskCreateRequest(BaseModel):
    """Request schema for creating a new task"""
    keyword: str = Field(..., min_length=1, max_length=255, description="搜尋關鍵字")
    city: str = Field(..., min_length=1, max_length=100, description="城市")
    country: str = Field(default="ID", min_length=2, max_length=2, description="國家代碼")
    target_platforms: List[str] = Field(..., min_items=1, description="目標平台")
    max_results: int = Field(default=100, ge=1, le=1000, description="最大結果數")
    created_by: Optional[str] = Field(None, max_length=100, description="建立者")
    
    @validator('target_platforms')
    def validate_platforms(cls, v):
        """Validate target platforms"""
        valid_platforms = {'website', 'facebook', 'instagram'}
        for platform in v:
            if platform not in valid_platforms:
                raise ValueError(f"Invalid platform: {platform}. Must be one of {valid_platforms}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "keyword": "SMA Internasional",
                "city": "Jakarta",
                "target_platforms": ["website", "facebook"],
                "max_results": 100,
                "created_by": "admin"
            }
        }


class TaskResponse(BaseModel):
    """Response schema for task"""
    id: UUID
    keyword: str
    city: str
    country: str
    target_platforms: List[str]
    max_results: int
    status: str
    progress: int
    results_count: int
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_by: Optional[str]
    
    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Response schema for task list"""
    total: int
    skip: int
    limit: int
    tasks: List[TaskResponse]


# ============================================================================
# Contact Schemas
# ============================================================================

class ContactResponse(BaseModel):
    """Response schema for contact"""
    id: UUID
    task_id: UUID
    country: str
    city: Optional[str] = None
    keyword: Optional[str]
    institution_name: str
    institution_type: Optional[str]
    source_url: str
    source_platform: str
    email: Optional[str]
    whatsapp: Optional[str]
    additional_info: Optional[Dict[str, Any]]
    quality_score: Optional[float]
    is_verified: bool
    extracted_at: datetime
    
    class Config:
        from_attributes = True


class ContactListResponse(BaseModel):
    """Response schema for contact list"""
    total: int
    skip: int
    limit: int
    contacts: List[ContactResponse]


class ContactFilterParams(BaseModel):
    """Filter parameters for contact queries"""
    country: Optional[str] = None
    institution_type: Optional[str] = None
    city: Optional[str] = None
    source_platform: Optional[str] = None
    min_quality_score: Optional[float] = Field(None, ge=0, le=100)
    has_email: Optional[bool] = None
    has_whatsapp: Optional[bool] = None
    is_verified: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


# ============================================================================
# Scraping Log Schemas
# ============================================================================

class ScrapingLogResponse(BaseModel):
    """Response schema for scraping log"""
    id: UUID
    task_id: UUID
    url: str
    action: str
    status: str
    error_message: Optional[str]
    response_time: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ScrapingLogListResponse(BaseModel):
    """Response schema for scraping log list"""
    total: int
    skip: int
    limit: int
    logs: List[ScrapingLogResponse]


# ============================================================================
# Statistics Schemas
# ============================================================================

class TaskStatistics(BaseModel):
    """Task statistics"""
    total_tasks: int
    pending_tasks: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: int


class ContactStatistics(BaseModel):
    """Contact statistics"""
    total_contacts: int
    contacts_with_email: int
    contacts_with_whatsapp: int
    contacts_with_both: int
    average_quality_score: Optional[float]
    by_institution_type: Dict[str, int]
    by_platform: Dict[str, int]


class ScrapingStatistics(BaseModel):
    """Scraping statistics"""
    total_logs: int
    success_count: int
    error_count: int
    error_rate: float
    average_response_time: Optional[float]


class SystemStatistics(BaseModel):
    """System-wide statistics"""
    tasks: TaskStatistics
    contacts: ContactStatistics
    scraping: ScrapingStatistics


# ============================================================================
# Export Schemas
# ============================================================================

class ExportRequest(BaseModel):
    """Request schema for exporting contacts"""
    country: Optional[str] = Field(None, description="國家代碼篩選")
    keyword: Optional[str] = Field(None, description="關鍵字篩選")
    city: Optional[str] = Field(None, description="城市篩選")
    institution_type: Optional[str] = Field(None, description="機構類型篩選")
    source_platform: Optional[str] = Field(None, description="來源平台篩選")
    min_quality_score: Optional[float] = Field(None, ge=0, le=100, description="最低品質分數")
    has_email: Optional[bool] = Field(None, description="是否有Email")
    has_whatsapp: Optional[bool] = Field(None, description="是否有WhatsApp")
    date_from: Optional[datetime] = Field(None, description="開始日期")
    date_to: Optional[datetime] = Field(None, description="結束日期")
    max_records: Optional[int] = Field(None, ge=1, le=10000, description="最大記錄數")
    
    class Config:
        json_schema_extra = {
            "example": {
                "institution_type": "高中",
                "source_platform": "website",
                "min_quality_score": 50.0,
                "has_email": True,
                "date_from": "2024-01-01T00:00:00",
                "date_to": "2024-12-31T23:59:59",
                "max_records": 1000
            }
        }


class ExportResponse(BaseModel):
    """Response schema for export request"""
    task_id: str = Field(..., description="匯出任務ID")
    status: str = Field(..., description="任務狀態")
    message: str = Field(..., description="訊息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "pending",
                "message": "Export task created successfully"
            }
        }


class ExportStatusResponse(BaseModel):
    """Response schema for export status"""
    task_id: str
    status: str
    progress: Optional[int] = None
    filename: Optional[str] = None
    download_url: Optional[str] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# ============================================================================
# Common Response Schemas
# ============================================================================

class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    detail: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    status_code: int
