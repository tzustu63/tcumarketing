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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
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
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD
    )
