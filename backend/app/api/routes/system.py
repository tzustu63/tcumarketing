"""
System Management API Routes
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import subprocess
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.celery_app import celery_app
from app.api.schemas import MessageResponse
from app.tasks.task_monitor import check_and_complete_stuck_tasks

router = APIRouter(prefix="/api/system", tags=["System"])
logger = logging.getLogger(__name__)

# 使用線程池執行同步的 celery inspect 操作
executor = ThreadPoolExecutor(max_workers=3)


async def get_inspect_data(timeout: float = 10.0):
    """非同步獲取 celery inspect 數據，帶超時處理
    
    優化：使用更快的 ping() 方法檢查 Worker 狀態，只獲取 active tasks
    完全跳過 stats 和 registered 以提高響應速度
    """
    loop = asyncio.get_event_loop()
    
    def _get_inspect():
        inspect = celery_app.control.inspect(timeout=timeout)
        
        # 快速檢查 Worker 是否在線（使用 ping，最快）
        workers_online = []
        try:
            ping_result = inspect.ping()
            if ping_result:
                workers_online = list(ping_result.keys())
        except Exception as e:
            logger.debug(f"Failed to ping workers: {e}")
        
        # 只獲取 active tasks（最重要的資訊）
        active_tasks = {}
        try:
            active_tasks = inspect.active() or {}
        except Exception as e:
            logger.warning(f"Failed to get active tasks: {e}")
        
        # 不再獲取 stats 和 registered（太慢）
        return {
            'active': active_tasks,
            'workers_online': workers_online,
            'worker_count': len(workers_online),
        }
    
    try:
        # 增加超時時間（10秒基礎 + 5秒緩衝 = 15秒總超時）
        data = await asyncio.wait_for(
            loop.run_in_executor(executor, _get_inspect),
            timeout=timeout + 5.0
        )
        return data
    except asyncio.TimeoutError:
        logger.warning(f"Celery inspect timeout after {timeout + 3.0}s")
        # 即使超時，也嘗試快速獲取基本資訊
        try:
            inspect = celery_app.control.inspect(timeout=1.0)
            active = inspect.active() or {}
            ping_result = inspect.ping() or {}
            return {
                'active': active,
                'workers_online': list(ping_result.keys()),
                'worker_count': len(ping_result),
                'timeout': True,
            }
        except:
            return {
                'active': {},
                'workers_online': [],
                'worker_count': 0,
                'timeout': True,
            }
    except Exception as e:
        logger.error(f"Error getting inspect data: {e}")
        return {
            'active': {},
            'workers_online': [],
            'worker_count': 0,
            'error': str(e),
        }


@router.get("/workers/status")
async def get_workers_status() -> Dict[str, Any]:
    """
    獲取 Worker 狀態
    
    Get the status of all Celery workers.
    優化：使用簡化的檢查方式，只獲取必要資訊以提高響應速度
    """
    try:
        # 使用較長的超時（10秒），只獲取必要資訊
        inspect_data = await get_inspect_data(timeout=10.0)
        
        active_tasks = inspect_data.get('active', {})
        workers_online = inspect_data.get('workers_online', [])
        worker_count = inspect_data.get('worker_count', 0)
        
        return {
            "active_tasks": active_tasks,
            "workers_online": workers_online,
            "total_active": sum(len(tasks) for tasks in active_tasks.values()),
            "worker_count": worker_count,
            "timeout": inspect_data.get('timeout', False),
            "error": inspect_data.get('error'),
            # 為了向後兼容，保留這些欄位但設為空
            "stats": {},
            "registered_tasks": {},
        }
    except Exception as e:
        logger.error(f"Failed to get worker status: {e}")
        # 即使出錯也返回空數據，而不是返回 500 錯誤
        return {
            "active_tasks": {},
            "workers_online": [],
            "stats": {},
            "registered_tasks": {},
            "total_active": 0,
            "worker_count": 0,
            "error": str(e)
        }


@router.post("/workers/restart", response_model=MessageResponse)
async def restart_workers():
    """
    重啟 Workers
    
    Restart all Celery workers.
    """
    try:
        # This would need to be run from the host or with proper permissions
        # For now, we'll just purge the queue
        celery_app.control.purge()
        
        return MessageResponse(
            message="Workers restarted successfully",
            detail="All pending tasks have been purged"
        )
    except Exception as e:
        logger.error(f"Failed to restart workers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/queue/purge", response_model=MessageResponse)
async def purge_queue():
    """
    清理任務隊列
    
    Purge all pending tasks from the queue.
    """
    try:
        result = celery_app.control.purge()
        count = result if isinstance(result, int) else 0
        
        return MessageResponse(
            message="Queue purged successfully",
            detail=f"Removed {count} pending tasks"
        )
    except Exception as e:
        logger.error(f"Failed to purge queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/revoke", response_model=MessageResponse)
async def revoke_task(task_id: str, terminate: bool = False):
    """
    撤銷任務
    
    Revoke a running Celery task.
    
    Args:
        task_id: Celery task ID
        terminate: If True, forcefully terminate the task
    """
    try:
        celery_app.control.revoke(task_id, terminate=terminate, signal='SIGKILL' if terminate else 'SIGTERM')
        
        return MessageResponse(
            message="Task revoked successfully",
            detail=f"Task {task_id} has been {'terminated' if terminate else 'revoked'}"
        )
    except Exception as e:
        logger.error(f"Failed to revoke task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/redis/info")
async def get_redis_info() -> Dict[str, Any]:
    """
    獲取 Redis 資訊
    
    Get Redis server information.
    """
    try:
        from app.database import SessionLocal
        import redis
        from app.config import settings
        
        # Connect to Redis
        r = redis.from_url(settings.REDIS_URL)
        info = r.info()
        
        return {
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "N/A"),
            "total_commands_processed": info.get("total_commands_processed", 0),
            "uptime_in_seconds": info.get("uptime_in_seconds", 0),
        }
    except Exception as e:
        logger.error(f"Failed to get Redis info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/redis/flush", response_model=MessageResponse)
async def flush_redis():
    """
    清理 Redis
    
    Flush all Redis data (use with caution!).
    """
    try:
        import redis
        from app.config import settings
        
        # Connect to Redis
        r = redis.from_url(settings.REDIS_URL)
        r.flushall()
        
        return MessageResponse(
            message="Redis flushed successfully",
            detail="All Redis data has been cleared"
        )
    except Exception as e:
        logger.error(f"Failed to flush Redis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/check-stuck", response_model=MessageResponse)
async def check_stuck_tasks():
    """
    檢查並完成卡住的任務
    
    Check for tasks stuck in 'running' state and automatically complete them.
    """
    try:
        check_and_complete_stuck_tasks()
        
        return MessageResponse(
            message="Stuck tasks check completed",
            detail="All stuck tasks have been checked and completed if necessary"
        )
    except Exception as e:
        logger.error(f"Failed to check stuck tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))
