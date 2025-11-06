"""
Export API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from pathlib import Path
import logging

from app.api.dependencies import get_db
from app.api.schemas import (
    ExportRequest,
    ExportResponse,
    ExportStatusResponse,
    MessageResponse
)
from app.celery_app import celery_app
from app.config import settings

router = APIRouter(prefix="/api/contacts", tags=["Export"])
logger = logging.getLogger(__name__)


@router.post("/export", response_model=ExportResponse)
async def create_export_task(
    export_request: ExportRequest,
    db: Session = Depends(get_db)
):
    """
    建立匯出任務
    
    Create an export task to generate Excel file with filtered contacts.
    The task will be processed asynchronously by Celery worker.
    """
    try:
        # Import here to avoid circular dependency
        from app.tasks.scraping_tasks import export_data_task
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"contacts_export_{timestamp}.xlsx"
        
        # Create Celery task
        task = export_data_task.apply_async(
            kwargs={
                'filename': filename,
                'country': export_request.country,
                'keyword': export_request.keyword,
                'city': export_request.city,
                'institution_type': export_request.institution_type,
                'source_platform': export_request.source_platform,
                'min_quality_score': export_request.min_quality_score,
                'has_email': export_request.has_email,
                'has_whatsapp': export_request.has_whatsapp,
                'date_from': export_request.date_from.isoformat() if export_request.date_from else None,
                'date_to': export_request.date_to.isoformat() if export_request.date_to else None,
                'max_records': export_request.max_records
            }
        )
        
        logger.info(f"Export task created: {task.id}")
        
        return ExportResponse(
            task_id=task.id,
            status="pending",
            message="Export task created successfully. Use the task_id to check status."
        )
        
    except Exception as e:
        logger.error(f"Failed to create export task: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create export task: {str(e)}"
        )


@router.get("/export/{task_id}/status", response_model=ExportStatusResponse)
async def get_export_status(task_id: str):
    """
    獲取匯出任務狀態
    
    Get the status of an export task.
    """
    try:
        # Get task result from Celery
        task_result = celery_app.AsyncResult(task_id)
        
        response = ExportStatusResponse(
            task_id=task_id,
            status=task_result.state.lower()
        )
        
        if task_result.state == 'PENDING':
            response.progress = 0
            
        elif task_result.state == 'STARTED':
            response.progress = 50
            
        elif task_result.state == 'SUCCESS':
            response.progress = 100
            result = task_result.result
            if isinstance(result, dict):
                response.filename = result.get('filename')
                response.download_url = f"/api/contacts/export/{task_id}/download"
                response.completed_at = datetime.fromisoformat(result.get('completed_at')) if result.get('completed_at') else None
            
        elif task_result.state == 'FAILURE':
            response.progress = 0
            response.error = str(task_result.info)
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to get export status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get export status: {str(e)}"
        )


@router.get("/export/{task_id}/download")
async def download_export_file(task_id: str):
    """
    下載匯出檔案
    
    Download the exported Excel file.
    """
    try:
        # Get task result
        task_result = celery_app.AsyncResult(task_id)
        
        if task_result.state != 'SUCCESS':
            raise HTTPException(
                status_code=400,
                detail=f"Export task is not completed yet. Current status: {task_result.state}"
            )
        
        result = task_result.result
        if not isinstance(result, dict) or 'filepath' not in result:
            raise HTTPException(
                status_code=500,
                detail="Export task result is invalid"
            )
        
        filepath = Path(result['filepath'])
        
        if not filepath.exists():
            raise HTTPException(
                status_code=404,
                detail="Export file not found"
            )
        
        filename = result.get('filename', filepath.name)
        
        return FileResponse(
            path=str(filepath),
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download export file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download export file: {str(e)}"
        )


@router.delete("/export/{task_id}", response_model=MessageResponse)
async def delete_export_file(task_id: str):
    """
    刪除匯出檔案
    
    Delete the exported file and task result.
    """
    try:
        # Get task result
        task_result = celery_app.AsyncResult(task_id)
        
        if task_result.state == 'SUCCESS':
            result = task_result.result
            if isinstance(result, dict) and 'filepath' in result:
                filepath = Path(result['filepath'])
                if filepath.exists():
                    filepath.unlink()
                    logger.info(f"Deleted export file: {filepath}")
        
        # Forget task result
        task_result.forget()
        
        return MessageResponse(
            message="Export file and task result deleted successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to delete export file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete export file: {str(e)}"
        )
