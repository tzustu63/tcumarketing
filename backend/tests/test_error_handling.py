"""
Tests for error handling and logging system.
"""

import pytest
from app.exceptions import (
    AppException,
    ScrapingException,
    ValidationException,
    TaskNotFoundException
)


def test_app_exception():
    """Test base AppException."""
    exc = AppException(
        message="Test error",
        error_code="TEST_ERROR",
        status_code=500,
        details={"key": "value"}
    )
    
    assert exc.message == "Test error"
    assert exc.error_code == "TEST_ERROR"
    assert exc.status_code == 500
    assert exc.details == {"key": "value"}


def test_scraping_exception():
    """Test ScrapingException."""
    url = "https://example.com"
    exc = ScrapingException(
        message="Failed to scrape",
        url=url,
        details={"status_code": 404}
    )
    
    assert exc.message == "Failed to scrape"
    assert exc.error_code == "SCRAPING_ERROR"
    assert exc.status_code == 500
    assert exc.details["url"] == url
    assert exc.details["status_code"] == 404


def test_validation_exception():
    """Test ValidationException."""
    exc = ValidationException(
        message="Invalid email",
        field="email",
        details={"value": "invalid"}
    )
    
    assert exc.message == "Invalid email"
    assert exc.error_code == "VALIDATION_ERROR"
    assert exc.status_code == 400
    assert exc.details["field"] == "email"


def test_task_not_found_exception():
    """Test TaskNotFoundException."""
    task_id = "task-123"
    exc = TaskNotFoundException(task_id=task_id)
    
    assert "task-123" in exc.message
    assert exc.error_code == "TASK_NOT_FOUND"
    assert exc.status_code == 404
    assert exc.details["task_id"] == task_id


def test_exception_inheritance():
    """Test that custom exceptions inherit from AppException."""
    assert issubclass(ScrapingException, AppException)
    assert issubclass(ValidationException, AppException)
    assert issubclass(TaskNotFoundException, AppException)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
