"""
Logging configuration for the application.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from app.config import settings


class DatabaseLogHandler(logging.Handler):
    """Custom log handler that writes logs to the database."""
    
    def __init__(self, db_session_factory=None):
        super().__init__()
        self.db_session_factory = db_session_factory
    
    def emit(self, record: logging.LogRecord):
        """Emit a log record to the database."""
        try:
            if not self.db_session_factory:
                return
            
            # Only log errors and critical messages to database
            if record.levelno < logging.ERROR:
                return
            
            from app.models.scraping_log import ScrapingLog
            from sqlalchemy.orm import Session
            
            db: Session = self.db_session_factory()
            try:
                # Extract additional context from record
                task_id = getattr(record, 'task_id', None)
                url = getattr(record, 'url', None)
                action = getattr(record, 'action', 'unknown')
                
                log_entry = ScrapingLog(
                    task_id=task_id,
                    url=url or 'N/A',
                    action=action,
                    status='error' if record.levelno >= logging.ERROR else 'warning',
                    error_message=self.format(record),
                    response_time=None
                )
                
                db.add(log_entry)
                db.commit()
            except Exception as e:
                # Don't let logging errors crash the application
                print(f"Error writing log to database: {e}", file=sys.stderr)
            finally:
                db.close()
        except Exception:
            # Silently fail to prevent logging errors from crashing the app
            pass


class CustomFormatter(logging.Formatter):
    """Custom formatter with color support for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with optional colors."""
        
        # Create format string
        log_format = (
            '%(asctime)s - %(name)s - %(levelname)s - '
            '%(message)s'
        )
        
        # Add extra fields if present
        if hasattr(record, 'task_id') and record.task_id:
            log_format += ' [task_id=%(task_id)s]'
        if hasattr(record, 'url') and record.url:
            log_format += ' [url=%(url)s]'
        
        # Apply colors for console output
        if self.use_colors and sys.stderr.isatty():
            levelname = record.levelname
            color = self.COLORS.get(levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{levelname}{self.COLORS['RESET']}"
        
        formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    db_session_factory=None
) -> None:
    """
    Configure application logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        db_session_factory: Optional database session factory for DB logging
    """
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(CustomFormatter(use_colors=True))
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotating file handler (max 10MB, keep 5 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(CustomFormatter(use_colors=False))
        root_logger.addHandler(file_handler)
    
    # Database handler (if session factory provided)
    if db_session_factory:
        db_handler = DatabaseLogHandler(db_session_factory)
        db_handler.setLevel(logging.ERROR)
        root_logger.addHandler(db_handler)
    
    # Set specific loggers
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('celery').setLevel(logging.INFO)
    
    # Log startup message
    root_logger.info(f"Logging configured with level: {log_level}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LogContext:
    """Context manager for adding extra context to log records."""
    
    def __init__(self, logger: logging.Logger, **kwargs):
        self.logger = logger
        self.context = kwargs
        self.old_factory = None
    
    def __enter__(self):
        self.old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)


def log_scraping_activity(
    logger: logging.Logger,
    task_id: Optional[str],
    url: str,
    action: str,
    status: str,
    error_message: Optional[str] = None,
    response_time: Optional[int] = None
):
    """
    Log scraping activity with structured data.
    
    Args:
        logger: Logger instance
        task_id: Task ID
        url: URL being scraped
        action: Action being performed
        status: Status of the action
        error_message: Optional error message
        response_time: Optional response time in milliseconds
    """
    
    extra = {
        'task_id': task_id,
        'url': url,
        'action': action,
        'response_time': response_time
    }
    
    if status == 'success':
        logger.info(f"Scraping {action} succeeded for {url}", extra=extra)
    elif status == 'error':
        logger.error(f"Scraping {action} failed for {url}: {error_message}", extra=extra)
    else:
        logger.warning(f"Scraping {action} status {status} for {url}", extra=extra)


def log_extraction_activity(
    logger: logging.Logger,
    task_id: Optional[str],
    url: str,
    extracted_data: dict,
    success: bool = True
):
    """
    Log extraction activity.
    
    Args:
        logger: Logger instance
        task_id: Task ID
        url: URL being processed
        extracted_data: Extracted data
        success: Whether extraction was successful
    """
    
    extra = {
        'task_id': task_id,
        'url': url,
        'action': 'extract_contact'
    }
    
    if success:
        logger.info(
            f"Extracted contact info from {url}: "
            f"email={extracted_data.get('email', 'N/A')}, "
            f"whatsapp={extracted_data.get('whatsapp', 'N/A')}",
            extra=extra
        )
    else:
        logger.warning(f"Failed to extract contact info from {url}", extra=extra)


# Initialize logging on module import
if hasattr(settings, 'LOG_LEVEL'):
    log_level = settings.LOG_LEVEL
else:
    log_level = "INFO"

log_file = "logs/app.log" if Path("logs").exists() or Path("logs").parent.exists() else None

setup_logging(log_level=log_level, log_file=log_file)
