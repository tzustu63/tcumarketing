"""
Application Configuration
"""
from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/recruitment"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    
    # CORS - Allow all origins in production (or specify comma-separated list)
    CORS_ORIGINS: str = "*"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from string to list"""
        # 如果值為 "*"，直接返回
        if self.CORS_ORIGINS == "*":
            return ["*"]
        
        # 如果值是 JSON 數組格式（包含方括號），先去除方括號和引號
        cors_str = str(self.CORS_ORIGINS).strip()
        if cors_str.startswith("[") and cors_str.endswith("]"):
            # 去除方括號
            cors_str = cors_str[1:-1]
            # 分割並清理引號和空格
            origins = [
                origin.strip().strip('"').strip("'")
                for origin in cors_str.split(",")
                if origin.strip()
            ]
            return origins if origins else ["*"]
        
        # 如果是逗號分隔的字符串
        if isinstance(self.CORS_ORIGINS, str) and "," in cors_str:
            origins = [
                origin.strip().strip('"').strip("'")
                for origin in cors_str.split(",")
                if origin.strip()
            ]
            return origins if origins else ["*"]
        
        # 單個字符串
        if isinstance(self.CORS_ORIGINS, str) and cors_str:
            return [cors_str.strip('"').strip("'")]
        
        # 預設允許所有來源
        return ["*"]

    @property
    def celery_broker_url(self) -> str:
        """Return resolved Celery broker URL with Redis fallback"""
        return self.CELERY_BROKER_URL or self.REDIS_URL

    @property
    def celery_result_backend(self) -> str:
        """Return resolved Celery backend URL with Redis fallback"""
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL
    
    # Scraping
    SCRAPING_HEADLESS: bool = True
    SCRAPING_USER_AGENTS: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    SCRAPING_MIN_DELAY: int = 2
    SCRAPING_MAX_DELAY: int = 5
    SCRAPING_MAX_RETRIES: int = 3
    
    # Google Custom Search API
    GOOGLE_API_KEY: str = ""
    GOOGLE_CSE_ID: str = ""
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_MAX_REQUESTS_PER_DOMAIN: int = 10
    RATE_LIMIT_DOMAIN_TIME_WINDOW: int = 60
    RATE_LIMIT_MIN_REQUEST_INTERVAL: float = 2.0
    RATE_LIMIT_MAX_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_MAX_CONCURRENT_REQUESTS: int = 10
    
    # Task
    TASK_TIMEOUT: int = 300
    TASK_MAX_WORKERS: int = 4
    TASK_PRIORITY_ENABLED: bool = True
    
    # Export
    EXPORT_DIR: str = "./exports"
    EXPORT_MAX_RECORDS: int = 10000
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
