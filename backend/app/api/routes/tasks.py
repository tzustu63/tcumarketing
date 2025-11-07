"""
Task Management API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.api.dependencies import get_db
from app.api.schemas import (
    TaskCreateRequest,
    TaskResponse,
    TaskListResponse,
    MessageResponse
)
from app.repositories.task_repository import TaskRepository
from app.repositories.stored_keyword_repository import StoredKeywordRepository
from app.models.task import Task
from app.tasks.scraping_tasks import scrape_google_task

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    task_data: TaskCreateRequest,
    db: Session = Depends(get_db)
):
    """
    建立新任務並自動啟動
    
    Create a new search task and automatically start execution.
    """
    task_repo = TaskRepository(db)
    
    # Create task data dictionary with running status
    task_data_dict = {
        "keyword": task_data.keyword,
        "city": task_data.city,
        "country": task_data.country,
        "target_platforms": task_data.target_platforms,
        "max_results": task_data.max_results,
        "status": "running",  # 直接設為 running
        "progress": 0,
        "results_count": 0,
        "created_by": task_data.created_by,
        "started_at": datetime.utcnow()  # 設定啟動時間
    }
    
    # Save to database
    created_task = task_repo.create(task_data_dict)
    
    # Automatically store keyword and city for future use
    try:
        stored_repo = StoredKeywordRepository(db)
        stored_repo.add_keyword(task_data.country, task_data.keyword)
        stored_repo.add_city(task_data.country, task_data.city)
    except Exception as e:
        # Log error but don't fail the task creation
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to store keyword/city: {e}")
    
    # Automatically queue the task for execution
    try:
        # 使用 apply_async 並設置超時，避免長時間等待
        scrape_google_task.apply_async(
            args=[str(created_task.id)],
            expires=300  # 任務在 5 分鐘內必須被執行
        )
    except Exception as e:
        # If queueing fails, update status to failed but still return the task
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to queue task {created_task.id}: {str(e)}")
        
        task_repo.update(str(created_task.id), {
            "status": "failed",
            "error_message": f"Failed to queue task: {str(e)}. Please check if Celery workers are running."
        })
        
        # 不拋出異常，而是返回任務（狀態已更新為 failed）
        # 這樣前端可以看到任務已創建但啟動失敗
        created_task.status = "failed"
        created_task.error_message = f"Failed to queue task: {str(e)}. Please check if Celery workers are running."
    
    return created_task


@router.get("", response_model=TaskListResponse)
async def get_tasks(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    country: Optional[str] = Query(None, description="Filter by country code"),
    db: Session = Depends(get_db)
):
    """
    獲取任務列表
    
    Get a list of tasks with optional filtering and pagination.
    """
    task_repo = TaskRepository(db)
    
    # Build query
    query = db.query(Task)
    
    if status:
        query = query.filter(Task.status == status)
    
    if country:
        query = query.filter(Task.country == country)
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering
    tasks = (
        query
        .order_by(Task.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return TaskListResponse(
        total=total,
        skip=skip,
        limit=limit,
        tasks=tasks
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    db: Session = Depends(get_db)
):
    """
    獲取任務詳情
    
    Get detailed information about a specific task.
    """
    task_repo = TaskRepository(db)
    task = task_repo.get(str(task_id))
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return task


@router.post("/{task_id}/start", response_model=MessageResponse)
async def start_task(
    task_id: UUID,
    db: Session = Depends(get_db)
):
    """
    啟動任務
    
    Start executing a pending task.
    """
    task_repo = TaskRepository(db)
    task = task_repo.get(str(task_id))
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    if task.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Task cannot be started. Current status: {task.status}"
        )
    
    # Update task status to running
    update_data = {
        "status": "running",
        "started_at": datetime.utcnow()
    }
    task_repo.update(str(task_id), update_data)
    
    # Queue the task for execution
    try:
        scrape_google_task.delay(str(task_id))
    except Exception as e:
        # If queueing fails, revert status
        revert_data = {
            "status": "pending",
            "started_at": None
        }
        task_repo.update(str(task_id), revert_data)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue task: {str(e)}"
        )
    
    return MessageResponse(
        message="Task started successfully",
        detail=f"Task {task_id} has been queued for execution"
    )


@router.delete("/{task_id}", response_model=MessageResponse)
async def delete_task(
    task_id: UUID,
    db: Session = Depends(get_db)
):
    """
    刪除任務
    
    Delete a task and all associated data (contacts, logs).
    """
    task_repo = TaskRepository(db)
    task = task_repo.get(str(task_id))
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    if task.status == "running":
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a running task. Please wait for it to complete or fail."
        )
    
    # Delete task (cascade will delete related contacts and logs)
    task_repo.delete(str(task_id))
    
    return MessageResponse(
        message="Task deleted successfully",
        detail=f"Task {task_id} and all associated data have been deleted"
    )


@router.get("/{task_id}/progress", response_model=dict)
async def get_task_progress(
    task_id: UUID,
    db: Session = Depends(get_db)
):
    """
    獲取任務進度
    
    Get the current progress of a task.
    """
    task_repo = TaskRepository(db)
    task = task_repo.get(str(task_id))
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return {
        "task_id": task.id,
        "status": task.status,
        "progress": task.progress,
        "results_count": task.results_count,
        "started_at": task.started_at,
        "completed_at": task.completed_at,
        "error_message": task.error_message
    }
