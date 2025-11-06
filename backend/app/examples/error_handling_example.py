"""
Example usage of the error handling and logging system.

This file demonstrates how to use custom exceptions, logging, and monitoring
in the application.
"""

from app.exceptions import (
    ScrapingException,
    ExtractionException,
    ValidationException,
    CaptchaDetectedException
)
from app.logging_config import get_logger, log_scraping_activity, log_extraction_activity
from app.utils.logging_utils import log_scraping_success, log_scraping_error
from app.monitoring import MetricsCalculator, AlertManager

# Get logger instance
logger = get_logger(__name__)


def example_scraping_with_error_handling():
    """Example: Scraping with proper error handling."""
    
    url = "https://example.com"
    task_id = "task-123"
    
    try:
        # Simulate scraping operation
        logger.info(f"Starting to scrape {url}", extra={"task_id": task_id, "url": url})
        
        # If scraping fails, raise appropriate exception
        # raise ScrapingException(
        #     message="Failed to fetch page",
        #     url=url,
        #     details={"status_code": 404}
        # )
        
        # If CAPTCHA detected
        # raise CaptchaDetectedException(url=url)
        
        # Log successful scraping
        log_scraping_activity(
            logger=logger,
            task_id=task_id,
            url=url,
            action="fetch_page",
            status="success",
            response_time=250
        )
        
        logger.info(f"Successfully scraped {url}")
        
    except ScrapingException as e:
        logger.error(f"Scraping failed: {e.message}", extra={"task_id": task_id, "url": url})
        # Re-raise to be handled by FastAPI middleware
        raise
    
    except CaptchaDetectedException as e:
        logger.warning(f"CAPTCHA detected at {url}", extra={"task_id": task_id, "url": url})
        # Handle CAPTCHA (pause task, notify admin, etc.)
        raise


def example_extraction_with_logging():
    """Example: Contact extraction with logging."""
    
    url = "https://example.com/contact"
    task_id = "task-123"
    
    try:
        # Simulate extraction
        extracted_data = {
            "email": "info@example.com",
            "whatsapp": "+6281234567890"
        }
        
        # Validate extracted data
        if not extracted_data.get("email") and not extracted_data.get("whatsapp"):
            raise ExtractionException(
                message="No contact information found",
                details={"url": url}
            )
        
        # Log successful extraction
        log_extraction_activity(
            logger=logger,
            task_id=task_id,
            url=url,
            extracted_data=extracted_data,
            success=True
        )
        
        return extracted_data
        
    except ExtractionException as e:
        log_extraction_activity(
            logger=logger,
            task_id=task_id,
            url=url,
            extracted_data={},
            success=False
        )
        raise


def example_database_logging(db):
    """Example: Logging to database."""
    
    task_id = "task-123"
    url = "https://example.com"
    
    # Log successful operation
    log_scraping_success(
        db=db,
        task_id=task_id,
        url=url,
        action="google_search",
        response_time=150
    )
    
    # Log error
    log_scraping_error(
        db=db,
        task_id=task_id,
        url=url,
        action="fetch_page",
        error_message="Connection timeout after 30 seconds"
    )


def example_monitoring_and_alerts(db):
    """Example: Using monitoring and alerts."""
    
    # Calculate metrics
    metrics_calculator = MetricsCalculator(db)
    
    # Get task success rate for last 24 hours
    success_rate = metrics_calculator.calculate_task_success_rate(
        time_window_hours=24
    )
    print(f"Task success rate (24h): {success_rate}%")
    
    # Get error rate for specific task
    error_rate = metrics_calculator.calculate_error_rate(
        task_id="task-123",
        time_window_hours=1
    )
    print(f"Error rate for task-123 (1h): {error_rate}%")
    
    # Get comprehensive statistics
    stats = metrics_calculator.get_task_statistics(
        time_window_hours=24
    )
    print(f"Statistics: {stats}")
    
    # Get recent errors
    recent_errors = metrics_calculator.get_recent_errors(limit=5)
    print(f"Recent errors: {recent_errors}")
    
    # Check alerts
    alert_manager = AlertManager(db)
    
    # Check if error rate exceeds threshold
    error_alert = alert_manager.check_error_rate_threshold(
        threshold=20.0,
        time_window_hours=1
    )
    
    if error_alert["alert_triggered"]:
        print(f"⚠️ ALERT: Error rate {error_alert['error_rate']}% exceeds threshold!")
        # Send notification (email, Slack, etc.)
    
    # Check all alerts
    all_alerts = alert_manager.get_all_alerts()
    
    if all_alerts["any_alert_triggered"]:
        print("⚠️ One or more alerts triggered!")
        print(f"Alerts: {all_alerts['alerts']}")


def example_validation_with_exceptions():
    """Example: Data validation with custom exceptions."""
    
    email = "invalid-email"
    
    # Validate email format
    if "@" not in email or "." not in email:
        raise ValidationException(
            message="Invalid email format",
            field="email",
            details={"value": email, "expected_format": "user@domain.com"}
        )


# Example usage in a FastAPI endpoint
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.dependencies import get_db
from app.exceptions import ScrapingException, TaskNotFoundException

router = APIRouter()

@router.post("/api/tasks/{task_id}/scrape")
async def scrape_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    try:
        # Get task
        task = task_repo.get(task_id)
        if not task:
            raise TaskNotFoundException(task_id=task_id)
        
        # Perform scraping
        result = scrape_google(task.keyword, task.city)
        
        # Log success
        log_scraping_success(
            db=db,
            task_id=task_id,
            url=f"google.com/search?q={task.keyword}",
            action="google_search",
            response_time=result.get("response_time")
        )
        
        return {"status": "success", "results": result}
        
    except TaskNotFoundException:
        # Will be handled by middleware and return 404
        raise
    
    except ScrapingException as e:
        # Log error to database
        log_scraping_error(
            db=db,
            task_id=task_id,
            url=e.details.get("url", "unknown"),
            action="google_search",
            error_message=e.message
        )
        # Will be handled by middleware and return 500
        raise
"""


if __name__ == "__main__":
    print("Error Handling and Logging Examples")
    print("=" * 50)
    print("\nThis file contains examples of how to use:")
    print("1. Custom exceptions")
    print("2. Logging with context")
    print("3. Database logging")
    print("4. Monitoring and alerts")
    print("5. Validation with exceptions")
    print("\nSee the function definitions for detailed examples.")
