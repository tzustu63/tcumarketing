"""
Export API Routes
"""
import base64
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
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
from app.services.export_service import ExportService
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


@router.get("/export/download")
async def download_export_direct(
    export_request: ExportRequest = Depends(),
    db: Session = Depends(get_db)
):
    """Generate and stream export file directly without background task."""
    try:
        export_service = ExportService(db)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = export_request.max_records and \
            f"contacts_export_{timestamp}_top{export_request.max_records}.xlsx" \
            or f"contacts_export_{timestamp}.xlsx"

        result = export_service.export_contacts_to_excel_bytes(
            filename=filename,
            country=export_request.country,
            keyword=export_request.keyword,
            city=export_request.city,
            institution_type=export_request.institution_type,
            source_platform=export_request.source_platform,
            min_quality_score=export_request.min_quality_score,
            has_email=export_request.has_email,
            has_whatsapp=export_request.has_whatsapp,
            date_from=export_request.date_from,
            date_to=export_request.date_to,
            max_records=export_request.max_records
        )

        headers = {
            "Content-Disposition": f"attachment; filename={result['filename']}",
            "X-Records-Count": str(result["records_count"]),
        }

        return StreamingResponse(
            iter([result["content"]]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate export directly: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate export file")


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
                logger.info(
                    "Export task %s result keys: %s",
                    task_id,
                    list(result.keys())
                )
                response.filename = result.get('filename')
                response.download_url = f"/api/contacts/export/{task_id}/download"
                response.completed_at = datetime.fromisoformat(result.get('completed_at')) if result.get('completed_at') else None
            else:
                logger.warning(
                    "Export task %s returned unexpected result type: %s",
                    task_id,
                    type(result)
                )
            
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
async def download_export_file(
    task_id: str,
    db: Session = Depends(get_db)
):
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
        file_base64 = result.get('file_base64')
        filters_snapshot = result.get('filters')
        
        if not filepath.exists():
            logger.warning(
                "Export file missing on API container (task_id=%s, keys=%s)",
                task_id,
                list(result.keys())
            )
            if file_base64:
                try:
                    file_bytes = base64.b64decode(file_base64.encode('utf-8'))
                except Exception:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to decode export file"
                    )
                headers = {
                    "Content-Disposition": f"attachment; filename={result.get('filename', 'contacts_export.xlsx')}"
                }
                return StreamingResponse(
                    BytesIO(file_bytes),
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers=headers
                )
            elif filters_snapshot:
                export_service = ExportService(db)
                try:
                    regenerate = export_service.export_contacts_to_excel_bytes(
                        filename=result.get('filename', f"contacts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"),
                        country=filters_snapshot.get('country'),
                        keyword=filters_snapshot.get('keyword'),
                        city=filters_snapshot.get('city'),
                        institution_type=filters_snapshot.get('institution_type'),
                        source_platform=filters_snapshot.get('source_platform'),
                        min_quality_score=filters_snapshot.get('min_quality_score'),
                        has_email=filters_snapshot.get('has_email'),
                        has_whatsapp=filters_snapshot.get('has_whatsapp'),
                        date_from=datetime.fromisoformat(filters_snapshot['date_from']) if filters_snapshot.get('date_from') else None,
                        date_to=datetime.fromisoformat(filters_snapshot['date_to']) if filters_snapshot.get('date_to') else None,
                        max_records=filters_snapshot.get('max_records')
                    )
                except ValueError as e:
                    raise HTTPException(status_code=404, detail=str(e))

                headers = {
                    "Content-Disposition": f"attachment; filename={regenerate['filename']}",
                    "X-Records-Count": str(regenerate["records_count"]),
                }

                return StreamingResponse(
                    BytesIO(regenerate["content"]),
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers=headers
                )
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
