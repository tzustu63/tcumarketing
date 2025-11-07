"""
FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import tasks, contacts, stats, export, keywords
from app.middleware import register_exception_handlers

# Create FastAPI application
app = FastAPI(
    title="慈濟大學招生通路自動開發系統",
    description="Tzu Chi University Recruitment Automation System API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS
cors_origins = settings.cors_origins_list

# 當允許所有來源時，依據 FastAPI/Starlette 規範需停用 credentials
allow_credentials = not (len(cors_origins) == 1 and cors_origins[0] == "*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
register_exception_handlers(app)

# Register routers
app.include_router(tasks.router)
app.include_router(contacts.router)
app.include_router(stats.router)
app.include_router(export.router)
app.include_router(keywords.router)

# Import system router
from app.api.routes import system
app.include_router(system.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "慈濟大學招生通路自動開發系統 API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/api/docs"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    檢查 API、資料庫、Redis/Celery 的連接狀態
    """
    health_status = {
        "status": "healthy",
        "api": "ok",
        "database": "unknown",
        "celery": "unknown",
        "timestamp": None
    }
    
    from datetime import datetime
    health_status["timestamp"] = datetime.utcnow().isoformat()
    
    # Check database connection
    try:
        from app.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["database"] = "ok"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Celery/Redis connection
    try:
        from app.celery_app import celery_app
        # 簡單檢查 broker 連接，設置 1 秒超時
        inspect = celery_app.control.inspect(timeout=1.0)
        # 嘗試獲取 worker 狀態（快速失敗）
        stats = inspect.stats()
        if stats:
            health_status["celery"] = "ok"
        else:
            health_status["celery"] = "no_workers"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["celery"] = f"error: {str(e)[:100]}"  # 限制錯誤訊息長度
        health_status["status"] = "degraded"
    
    return health_status


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD
    )
