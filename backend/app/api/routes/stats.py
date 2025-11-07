"""
Statistics and Logs API Routes
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import Optional
from uuid import UUID

from app.api.dependencies import get_db
from app.api.schemas import (
    SystemStatistics,
    TaskStatistics,
    ContactStatistics,
    ScrapingStatistics,
    ScrapingLogListResponse
)
from app.repositories.task_repository import TaskRepository
from app.repositories.contact_repository import ContactRepository
from app.repositories.scraping_log_repository import ScrapingLogRepository
from app.models.task import Task
from app.models.contact import Contact
from app.models.scraping_log import ScrapingLog
from app.monitoring import MetricsCalculator, AlertManager

router = APIRouter(prefix="/api", tags=["Statistics & Logs"])


@router.get("/stats", response_model=SystemStatistics)
async def get_system_statistics(
    db: Session = Depends(get_db)
):
    """
    獲取系統統計資料
    
    Get comprehensive system-wide statistics including tasks, contacts, and scraping metrics.
    """
    task_repo = TaskRepository(db)
    contact_repo = ContactRepository(db)
    log_repo = ScrapingLogRepository(db)
    
    # Task statistics
    total_tasks = task_repo.count()
    pending_tasks = task_repo.count_by_status("pending")
    running_tasks = task_repo.count_by_status("running")
    completed_tasks = task_repo.count_by_status("completed")
    failed_tasks = task_repo.count_by_status("failed")
    
    task_stats = TaskStatistics(
        total_tasks=total_tasks,
        pending_tasks=pending_tasks,
        running_tasks=running_tasks,
        completed_tasks=completed_tasks,
        failed_tasks=failed_tasks
    )
    
    # Contact statistics
    total_contacts = contact_repo.count()
    with_email = db.query(Contact).filter(Contact.email.isnot(None)).count()
    with_whatsapp = db.query(Contact).filter(Contact.whatsapp.isnot(None)).count()
    with_both = db.query(Contact).filter(
        and_(Contact.email.isnot(None), Contact.whatsapp.isnot(None))
    ).count()
    
    avg_score = db.query(func.avg(Contact.quality_score)).scalar()
    
    # Get counts by institution type
    by_type = db.query(
        Contact.institution_type,
        func.count(Contact.id)
    ).group_by(Contact.institution_type).all()
    
    # Get counts by platform
    by_platform = db.query(
        Contact.source_platform,
        func.count(Contact.id)
    ).group_by(Contact.source_platform).all()
    
    contact_stats = ContactStatistics(
        total_contacts=total_contacts,
        contacts_with_email=with_email,
        contacts_with_whatsapp=with_whatsapp,
        contacts_with_both=with_both,
        average_quality_score=float(avg_score) if avg_score else None,
        by_institution_type={inst_type or "unknown": count for inst_type, count in by_type},
        by_platform={platform: count for platform, count in by_platform}
    )
    
    # Scraping statistics
    total_logs = log_repo.count()
    status_counts = log_repo.count_by_status()
    success_count = status_counts.get("success", 0)
    error_count = status_counts.get("error", 0)
    error_rate = log_repo.calculate_error_rate()
    avg_response_time = log_repo.get_average_response_time()
    
    scraping_stats = ScrapingStatistics(
        total_logs=total_logs,
        success_count=success_count,
        error_count=error_count,
        error_rate=error_rate,
        average_response_time=avg_response_time
    )
    
    return SystemStatistics(
        tasks=task_stats,
        contacts=contact_stats,
        scraping=scraping_stats
    )


@router.get("/logs", response_model=ScrapingLogListResponse)
async def get_scraping_logs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    task_id: Optional[UUID] = Query(None, description="Filter by task ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    errors_only: bool = Query(False, description="Show only error logs"),
    db: Session = Depends(get_db)
):
    """
    獲取爬取日誌
    
    Get scraping logs with filtering and pagination support.
    """
    log_repo = ScrapingLogRepository(db)
    
    # Build query
    query = db.query(ScrapingLog)
    
    if task_id:
        query = query.filter(ScrapingLog.task_id == task_id)
    
    if status:
        query = query.filter(ScrapingLog.status == status)
    
    if action:
        query = query.filter(ScrapingLog.action == action)
    
    if errors_only:
        query = query.filter(ScrapingLog.status == "error")
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering
    logs = (
        query
        .order_by(ScrapingLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return ScrapingLogListResponse(
        total=total,
        skip=skip,
        limit=limit,
        logs=logs
    )


@router.get("/logs/task/{task_id}", response_model=ScrapingLogListResponse)
async def get_task_logs(
    task_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    獲取特定任務的日誌
    
    Get all logs for a specific task.
    """
    log_repo = ScrapingLogRepository(db)
    
    logs = log_repo.get_by_task(str(task_id), skip=skip, limit=limit)
    total = db.query(ScrapingLog).filter(ScrapingLog.task_id == task_id).count()
    
    return ScrapingLogListResponse(
        total=total,
        skip=skip,
        limit=limit,
        logs=logs
    )


@router.get("/logs/errors", response_model=ScrapingLogListResponse)
async def get_error_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    task_id: Optional[UUID] = Query(None, description="Filter by task ID"),
    db: Session = Depends(get_db)
):
    """
    獲取錯誤日誌
    
    Get all error logs with optional task filtering.
    """
    log_repo = ScrapingLogRepository(db)
    
    logs = log_repo.get_errors(
        task_id=str(task_id) if task_id else None,
        skip=skip,
        limit=limit
    )
    
    # Get total error count
    query = db.query(ScrapingLog).filter(ScrapingLog.status == "error")
    if task_id:
        query = query.filter(ScrapingLog.task_id == task_id)
    total = query.count()
    
    return ScrapingLogListResponse(
        total=total,
        skip=skip,
        limit=limit,
        logs=logs
    )


@router.get("/stats/task/{task_id}", response_model=dict)
async def get_task_statistics(
    task_id: UUID,
    db: Session = Depends(get_db)
):
    """
    獲取特定任務的統計資料
    
    Get detailed statistics for a specific task.
    """
    task_repo = TaskRepository(db)
    contact_repo = ContactRepository(db)
    log_repo = ScrapingLogRepository(db)
    
    # Check if task exists
    task = task_repo.get(str(task_id))
    if not task:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # Contact statistics for this task
    contacts = contact_repo.get_by_task(str(task_id))
    total_contacts = len(contacts)
    with_email = sum(1 for c in contacts if c.email)
    with_whatsapp = sum(1 for c in contacts if c.whatsapp)
    with_both = sum(1 for c in contacts if c.email and c.whatsapp)
    
    # Calculate average quality score
    scores = [c.quality_score for c in contacts if c.quality_score is not None]
    avg_score = sum(scores) / len(scores) if scores else None
    
    # Scraping statistics for this task
    status_counts = log_repo.count_by_status(str(task_id))
    error_rate = log_repo.calculate_error_rate(str(task_id))
    avg_response_time = log_repo.get_average_response_time(str(task_id))
    
    return {
        "task_id": task.id,
        "task_status": task.status,
        "task_progress": task.progress,
        "contacts": {
            "total": total_contacts,
            "with_email": with_email,
            "with_whatsapp": with_whatsapp,
            "with_both": with_both,
            "average_quality_score": avg_score
        },
        "scraping": {
            "total_logs": sum(status_counts.values()),
            "status_counts": status_counts,
            "error_rate": error_rate,
            "average_response_time": avg_response_time
        }
    }



@router.get("/monitoring/metrics", response_model=dict)
async def get_monitoring_metrics(
    task_id: Optional[UUID] = Query(None, description="Filter by task ID"),
    time_window_hours: Optional[int] = Query(None, ge=1, le=168, description="Time window in hours"),
    db: Session = Depends(get_db)
):
    """
    獲取監控指標
    
    Get monitoring metrics including success rates, error rates, and statistics.
    """
    metrics_calculator = MetricsCalculator(db)
    
    task_id_str = str(task_id) if task_id else None
    
    statistics = metrics_calculator.get_task_statistics(
        task_id=task_id_str,
        time_window_hours=time_window_hours
    )
    
    recent_errors = metrics_calculator.get_recent_errors(
        limit=10,
        task_id=task_id_str
    )
    
    return {
        "statistics": statistics,
        "recent_errors": recent_errors,
        "time_window_hours": time_window_hours
    }


@router.get("/monitoring/alerts", response_model=dict)
async def get_alerts(
    task_id: Optional[UUID] = Query(None, description="Filter by task ID"),
    db: Session = Depends(get_db)
):
    """
    獲取告警狀態
    
    Get alert status including error rate and task failure rate alerts.
    """
    alert_manager = AlertManager(db)
    
    task_id_str = str(task_id) if task_id else None
    
    alerts = alert_manager.get_all_alerts(task_id=task_id_str)
    
    return alerts


@router.get("/monitoring/error-rate", response_model=dict)
async def check_error_rate(
    task_id: Optional[UUID] = Query(None, description="Filter by task ID"),
    threshold: float = Query(20.0, ge=0, le=100, description="Error rate threshold percentage"),
    time_window_hours: int = Query(1, ge=1, le=168, description="Time window in hours"),
    db: Session = Depends(get_db)
):
    """
    檢查錯誤率告警
    
    Check if error rate exceeds the specified threshold.
    """
    alert_manager = AlertManager(db)
    
    task_id_str = str(task_id) if task_id else None
    
    alert = alert_manager.check_error_rate_threshold(
        task_id=task_id_str,
        threshold=threshold,
        time_window_hours=time_window_hours
    )
    
    return alert


@router.get("/monitoring/success-rate", response_model=dict)
async def get_success_rate(
    task_id: Optional[UUID] = Query(None, description="Filter by task ID"),
    time_window_hours: Optional[int] = Query(None, ge=1, le=168, description="Time window in hours"),
    db: Session = Depends(get_db)
):
    """
    獲取任務成功率
    
    Get task success rate for the specified time window.
    """
    metrics_calculator = MetricsCalculator(db)
    
    task_id_str = str(task_id) if task_id else None
    
    success_rate = metrics_calculator.calculate_task_success_rate(
        task_id=task_id_str,
        time_window_hours=time_window_hours
    )
    
    error_rate = metrics_calculator.calculate_error_rate(
        task_id=task_id_str,
        time_window_hours=time_window_hours
    )
    
    return {
        "success_rate": success_rate,
        "error_rate": error_rate,
        "task_id": task_id_str,
        "time_window_hours": time_window_hours
    }
