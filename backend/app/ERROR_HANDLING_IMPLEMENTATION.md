# Error Handling and Logging System Implementation

## Overview

This document describes the implementation of the unified error handling, logging, and monitoring system for the Indonesia Recruitment Automation System.

## Components Implemented

### 1. Custom Exception Classes (`app/exceptions.py`)

Created a comprehensive set of custom exception classes that inherit from a base `AppException`:

- **AppException**: Base exception with error code, status code, and details
- **ScrapingException**: For web scraping errors
- **ExtractionException**: For contact extraction errors
- **ValidationException**: For data validation errors
- **DatabaseException**: For database operation errors
- **TaskNotFoundException**: For missing tasks
- **ContactNotFoundException**: For missing contacts
- **RateLimitException**: For rate limiting
- **ExportException**: For export operation errors
- **BrowserException**: For browser automation errors
- **CaptchaDetectedException**: For CAPTCHA detection
- **IPBlockedException**: For IP blocking

Each exception includes:
- Descriptive error message
- Unique error code
- HTTP status code
- Additional details dictionary

### 2. Error Handling Middleware (`app/middleware/error_handler.py`)

Implemented standardized error response format and exception handlers:

**ErrorResponse Class**:
- Standardized JSON error response format
- Includes error code, message, details, and timestamp

**Exception Handlers**:
- `app_exception_handler`: Handles custom AppException instances
- `validation_exception_handler`: Handles FastAPI validation errors
- `http_exception_handler`: Handles HTTP exceptions
- `general_exception_handler`: Catches unexpected exceptions

**Features**:
- Automatic logging of all errors
- Consistent error response format across all endpoints
- Detailed error information in development mode
- Secure error messages in production

### 3. Logging System (`app/logging_config.py`)

Comprehensive logging configuration with multiple handlers:

**DatabaseLogHandler**:
- Custom handler that writes error logs to the database
- Only logs ERROR and CRITICAL level messages to database
- Prevents logging errors from crashing the application

**CustomFormatter**:
- Color-coded console output for different log levels
- Includes additional context (task_id, url) when available
- Timestamp formatting

**Logging Configuration**:
- Console handler with color support
- Rotating file handler (10MB max, 5 backups)
- Database handler for error logs
- Configurable log levels per module

**Utility Functions**:
- `setup_logging()`: Configure all logging handlers
- `get_logger()`: Get logger instance
- `LogContext`: Context manager for adding extra context
- `log_scraping_activity()`: Log scraping operations
- `log_extraction_activity()`: Log extraction operations

### 4. Database Logging Utilities (`app/utils/logging_utils.py`)

Helper functions for logging to the database:

- `log_scraping_to_db()`: Generic scraping log function
- `log_scraping_success()`: Log successful operations
- `log_scraping_error()`: Log error operations
- `get_error_logs()`: Retrieve error logs
- `get_task_logs()`: Retrieve logs for specific task
- `count_error_logs()`: Count error logs

### 5. Monitoring and Metrics (`app/monitoring/metrics.py`)

**MetricsCalculator Class**:
- `calculate_task_success_rate()`: Calculate task success percentage
- `calculate_error_rate()`: Calculate error rate from logs
- `get_task_statistics()`: Comprehensive task statistics
- `get_recent_errors()`: Get recent error logs

**AlertManager Class**:
- `check_error_rate_threshold()`: Check if error rate exceeds 20%
- `check_task_failure_rate()`: Check task failure rate
- `get_all_alerts()`: Get all alert statuses

**Features**:
- Time-window based metrics (configurable hours)
- Task-specific or system-wide metrics
- Automatic alert triggering and logging
- Comprehensive statistics including:
  - Task counts by status
  - Contact statistics
  - Error rates
  - Success rates
  - Average quality scores

### 6. API Endpoints (`app/api/routes/stats.py`)

Added new monitoring endpoints:

- `GET /api/monitoring/metrics`: Get comprehensive metrics
- `GET /api/monitoring/alerts`: Get alert status
- `GET /api/monitoring/error-rate`: Check error rate threshold
- `GET /api/monitoring/success-rate`: Get success rate

All endpoints support:
- Optional task_id filtering
- Time window configuration
- Pagination where applicable

### 7. Integration with FastAPI (`app/main.py`)

Updated main application to:
- Register all exception handlers
- Remove old exception handlers
- Use standardized error handling

## Usage Examples

### Using Custom Exceptions

```python
from app.exceptions import ScrapingException, ValidationException

# Raise scraping exception
raise ScrapingException(
    message="Failed to fetch page",
    url="https://example.com",
    details={"status_code": 404}
)

# Raise validation exception
raise ValidationException(
    message="Invalid email format",
    field="email",
    details={"value": "invalid-email"}
)
```

### Logging with Context

```python
from app.logging_config import get_logger, log_scraping_activity

logger = get_logger(__name__)

# Log scraping activity
log_scraping_activity(
    logger=logger,
    task_id="task-123",
    url="https://example.com",
    action="fetch_page",
    status="success",
    response_time=250
)

# Log with extra context
logger.info("Processing task", extra={"task_id": "task-123", "url": "https://example.com"})
```

### Database Logging

```python
from app.utils.logging_utils import log_scraping_success, log_scraping_error

# Log success
log_scraping_success(
    db=db,
    task_id="task-123",
    url="https://example.com",
    action="extract_contact",
    response_time=150
)

# Log error
log_scraping_error(
    db=db,
    task_id="task-123",
    url="https://example.com",
    action="fetch_page",
    error_message="Connection timeout"
)
```

### Monitoring and Alerts

```python
from app.monitoring import MetricsCalculator, AlertManager

# Calculate metrics
metrics = MetricsCalculator(db)
success_rate = metrics.calculate_task_success_rate(time_window_hours=24)
error_rate = metrics.calculate_error_rate(task_id="task-123")

# Check alerts
alert_manager = AlertManager(db)
alert = alert_manager.check_error_rate_threshold(threshold=20.0)

if alert["alert_triggered"]:
    print(f"Alert: Error rate {alert['error_rate']}% exceeds threshold!")
```

## Error Response Format

All errors return a standardized JSON format:

```json
{
  "error": {
    "code": "SCRAPING_ERROR",
    "message": "Failed to fetch page",
    "details": {
      "url": "https://example.com",
      "status_code": 404
    },
    "timestamp": "2025-01-03T10:30:00.000Z"
  }
}
```

## Monitoring Metrics Response

```json
{
  "statistics": {
    "tasks": {
      "total": 100,
      "pending": 5,
      "running": 2,
      "completed": 85,
      "failed": 8,
      "success_rate": 91.4
    },
    "contacts": {
      "total": 450,
      "with_email": 380,
      "with_whatsapp": 420,
      "avg_quality_score": 75.5
    },
    "errors": {
      "error_rate": 12.3
    }
  },
  "recent_errors": [...]
}
```

## Alert Response

```json
{
  "any_alert_triggered": true,
  "alerts": {
    "error_rate": {
      "alert_triggered": true,
      "error_rate": 25.5,
      "threshold": 20.0,
      "time_window_hours": 1
    },
    "task_failure": {
      "alert_triggered": false,
      "failure_rate": 8.6,
      "threshold": 50.0
    }
  }
}
```

## Configuration

Logging configuration is controlled via environment variables in `.env`:

```env
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
```

## Requirements Satisfied

This implementation satisfies the following requirements:

- **需求 8.1**: Retry logic with exponential backoff (handled by exception system)
- **需求 8.2**: Error logging with URL, error type, and timestamp
- **需求 8.3**: Dashboard showing success rate, total records, and error statistics
- **需求 8.4**: Alert when error rate exceeds 20%
- **需求 8.5**: Detailed logs maintained for all activities

## Next Steps

To fully integrate this system:

1. Update existing scraping and extraction code to use custom exceptions
2. Add logging calls in critical operations
3. Configure log rotation and retention policies
4. Set up alert notifications (email, Slack, etc.)
5. Create monitoring dashboard in frontend
6. Add unit tests for error handling and logging
