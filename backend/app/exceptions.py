"""
Custom exception classes for the application.
"""

from typing import Optional, Dict, Any


class AppException(Exception):
    """Base exception class for all application exceptions."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ScrapingException(AppException):
    """Exception raised during web scraping operations."""
    
    def __init__(self, message: str, url: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if url:
            error_details["url"] = url
        super().__init__(
            message=message,
            error_code="SCRAPING_ERROR",
            status_code=500,
            details=error_details
        )


class ExtractionException(AppException):
    """Exception raised during contact information extraction."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="EXTRACTION_ERROR",
            status_code=500,
            details=details or {}
        )


class ValidationException(AppException):
    """Exception raised during data validation."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if field:
            error_details["field"] = field
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=error_details
        )


class DatabaseException(AppException):
    """Exception raised during database operations."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=500,
            details=details or {}
        )


class TaskNotFoundException(AppException):
    """Exception raised when a task is not found."""
    
    def __init__(self, task_id: str):
        super().__init__(
            message=f"Task with ID {task_id} not found",
            error_code="TASK_NOT_FOUND",
            status_code=404,
            details={"task_id": task_id}
        )


class ContactNotFoundException(AppException):
    """Exception raised when a contact is not found."""
    
    def __init__(self, contact_id: str):
        super().__init__(
            message=f"Contact with ID {contact_id} not found",
            error_code="CONTACT_NOT_FOUND",
            status_code=404,
            details={"contact_id": contact_id}
        )


class RateLimitException(AppException):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details
        )


class ExportException(AppException):
    """Exception raised during data export operations."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="EXPORT_ERROR",
            status_code=500,
            details=details or {}
        )


class BrowserException(AppException):
    """Exception raised during browser automation operations."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="BROWSER_ERROR",
            status_code=500,
            details=details or {}
        )


class CaptchaDetectedException(AppException):
    """Exception raised when CAPTCHA is detected."""
    
    def __init__(self, url: str):
        super().__init__(
            message=f"CAPTCHA detected at {url}",
            error_code="CAPTCHA_DETECTED",
            status_code=503,
            details={"url": url}
        )


class IPBlockedException(AppException):
    """Exception raised when IP is blocked."""
    
    def __init__(self, url: str):
        super().__init__(
            message=f"IP blocked while accessing {url}",
            error_code="IP_BLOCKED",
            status_code=503,
            details={"url": url}
        )
