# Error Handling & Logging - Quick Reference

## 🚀 Quick Start

### 1. Import What You Need

```python
# Exceptions
from app.exceptions import (
    ScrapingException,
    ExtractionException,
    ValidationException,
    TaskNotFoundException
)

# Logging
from app.logging_config import get_logger, log_scraping_activity
from app.utils.logging_utils import log_scraping_success, log_scraping_error

# Monitoring
from app.monitoring import MetricsCalculator, AlertManager
```

### 2. Raise Exceptions

```python
# Scraping error
raise ScrapingException(
    message="Failed to fetch page",
    url="https://example.com",
    details={"status_code": 404}
)

# Validation error
raise ValidationException(
    message="Invalid email format",
    field="email"
)

# Not found error
raise TaskNotFoundException(task_id="task-123")
```

### 3. Log Activities

```python
# Get logger
logger = get_logger(__name__)

# Log with context
logger.info("Processing task", extra={"task_id": "123", "url": "example.com"})

# Log scraping activity
log_scraping_activity(
    logger=logger,
    task_id="task-123",
    url="https://example.com",
    action="fetch_page",
    status="success",
    response_time=250
)
```

### 4. Log to Database

```python
# Success
log_scraping_success(
    db=db,
    task_id="task-123",
    url="https://example.com",
    action="extract_contact",
    response_time=150
)

# Error
log_scraping_error(
    db=db,
    task_id="task-123",
    url="https://example.com",
    action="fetch_page",
    error_message="Connection timeout"
)
```

### 5. Check Metrics & Alerts

```python
# Calculate metrics
metrics = MetricsCalculator(db)
success_rate = metrics.calculate_task_success_rate(time_window_hours=24)
error_rate = metrics.calculate_error_rate(task_id="task-123")

# Check alerts
alert_manager = AlertManager(db)
alert = alert_manager.check_error_rate_threshold(threshold=20.0)

if alert["alert_triggered"]:
    # Handle alert
    print(f"Error rate: {alert['error_rate']}%")
```

## 📋 Available Exceptions

| Exception | Status Code | Use Case |
|-----------|-------------|----------|
| `ScrapingException` | 500 | Web scraping failures |
| `ExtractionException` | 500 | Contact extraction failures |
| `ValidationException` | 400 | Data validation errors |
| `DatabaseException` | 500 | Database operation errors |
| `TaskNotFoundException` | 404 | Task not found |
| `ContactNotFoundException` | 404 | Contact not found |
| `RateLimitException` | 429 | Rate limit exceeded |
| `ExportException` | 500 | Export operation errors |
| `BrowserException` | 500 | Browser automation errors |
| `CaptchaDetectedException` | 503 | CAPTCHA detected |
| `IPBlockedException` | 503 | IP blocked |

## 🔌 API Endpoints

### Monitoring
```
GET /api/monitoring/metrics?task_id=xxx&time_window_hours=24
GET /api/monitoring/alerts?task_id=xxx
GET /api/monitoring/error-rate?threshold=20&time_window_hours=1
GET /api/monitoring/success-rate?task_id=xxx&time_window_hours=24
```

### Logs
```
GET /api/logs?skip=0&limit=100&errors_only=true
GET /api/logs/task/{task_id}
GET /api/logs/errors?task_id=xxx
```

### Statistics
```
GET /api/stats
GET /api/stats/task/{task_id}
```

## 🎯 Common Patterns

### Pattern 1: Scraping with Error Handling
```python
try:
    result = scrape_page(url)
    log_scraping_success(db, task_id, url, "fetch_page", response_time=100)
    return result
except Exception as e:
    log_scraping_error(db, task_id, url, "fetch_page", str(e))
    raise ScrapingException(message=str(e), url=url)
```

### Pattern 2: Validation with Custom Exception
```python
def validate_email(email: str):
    if "@" not in email:
        raise ValidationException(
            message="Invalid email format",
            field="email",
            details={"value": email}
        )
```

### Pattern 3: Monitoring in Background Task
```python
@celery_app.task
def scraping_task(task_id: str):
    db = SessionLocal()
    try:
        # Perform scraping
        result = scrape_google(query)
        
        # Check alerts after task
        alert_manager = AlertManager(db)
        alert = alert_manager.check_error_rate_threshold(
            task_id=task_id,
            threshold=20.0
        )
        
        if alert["alert_triggered"]:
            # Send notification
            send_alert_notification(alert)
    finally:
        db.close()
```

## ⚙️ Configuration

### Environment Variables
```env
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
```

### Log Levels
- `DEBUG`: Detailed information for debugging
- `INFO`: General information (default)
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical errors

## 📊 Error Response Format

All errors return this format:
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

## 🔔 Alert Thresholds

| Alert Type | Default Threshold | Time Window |
|------------|-------------------|-------------|
| Error Rate | 20% | 1 hour |
| Task Failure Rate | 50% | 24 hours |

## 💡 Tips

1. **Always use custom exceptions** instead of generic Exception
2. **Add context to logs** using the `extra` parameter
3. **Log to database for errors** to enable monitoring
4. **Check alerts periodically** in background tasks
5. **Use appropriate log levels** (don't log everything as ERROR)
6. **Include URLs in exceptions** for easier debugging
7. **Set up alert notifications** for production

## 📚 More Information

- Full documentation: `ERROR_HANDLING_IMPLEMENTATION.md`
- Examples: `app/examples/error_handling_example.py`
- Tests: `tests/test_error_handling.py`
