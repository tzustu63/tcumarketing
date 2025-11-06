# Task Queue System Documentation

## Overview

This task queue system implements asynchronous web scraping and data extraction using Celery and Redis. It provides three main tasks:

1. **scrape_google_task** - Scrapes Google search results
2. **extract_website_task** - Extracts contact information from websites
3. **extract_social_task** - Extracts contact information from social media

## Architecture

```
┌─────────────┐
│   FastAPI   │ ──► Creates tasks
└─────────────┘
       │
       ▼
┌─────────────┐
│    Redis    │ ──► Message queue
└─────────────┘
       │
       ▼
┌─────────────┐
│   Celery    │ ──► Executes tasks
│   Workers   │
└─────────────┘
       │
       ▼
┌─────────────┐
│ PostgreSQL  │ ──► Stores results
└─────────────┘
```

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Start Redis

Using Docker:
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

Or using Docker Compose (from project root):
```bash
docker-compose up -d redis
```

### 3. Configure Environment

Create `.env` file in backend directory:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/recruitment
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 4. Start Celery Worker

```bash
cd backend
celery -A app.celery_app worker --loglevel=info --concurrency=4
```

For development with auto-reload:
```bash
watchmedo auto-restart --directory=./app --pattern=*.py --recursive -- \
  celery -A app.celery_app worker --loglevel=info
```

### 5. Monitor Tasks (Optional)

Start Flower for web-based monitoring:
```bash
celery -A app.celery_app flower --port=5555
```

Access at: http://localhost:5555

## Task Details

### scrape_google_task

Scrapes Google search results and queues extraction tasks.

**Parameters:**
- `task_id` (str): UUID of the task in database

**Process:**
1. Fetches task from database
2. Builds search query from keyword and city
3. Scrapes Google results (up to 5 pages)
4. Filters results by target platforms
5. Queues extraction tasks for each result
6. Updates task progress and status

**Example:**
```python
from app.tasks import scrape_google_task

# Queue the task
result = scrape_google_task.delay("task-uuid-here")

# Check status
print(result.status)
print(result.result)
```

### extract_website_task

Extracts contact information from a website.

**Parameters:**
- `task_id` (str): UUID of the parent task
- `url` (str): Website URL to extract from
- `institution_name` (str): Name of the institution

**Process:**
1. Finds contact page on website
2. Fetches page content
3. Extracts emails and WhatsApp numbers
4. Validates contact information
5. Calculates quality score
6. Saves to database (if not duplicate)

**Example:**
```python
from app.tasks import extract_website_task

result = extract_website_task.delay(
    "task-uuid",
    "https://example.com",
    "Example School"
)
```

### extract_social_task

Extracts contact information from social media.

**Parameters:**
- `task_id` (str): UUID of the parent task
- `url` (str): Social media URL
- `platform` (str): Platform name ('facebook' or 'instagram')
- `page_name` (str): Name of the page/profile

**Process:**
1. Scrapes social media profile
2. Extracts bio/about information
3. Identifies contact markers (WA:, Email:, etc.)
4. Validates contact information
5. Calculates quality score
6. Saves to database (if not duplicate)

**Example:**
```python
from app.tasks import extract_social_task

result = extract_social_task.delay(
    "task-uuid",
    "https://facebook.com/example",
    "facebook",
    "Example Page"
)
```

## Error Handling

### Retry Mechanism

All tasks implement automatic retry with exponential backoff:

- **Max retries:** 3
- **Base delay:** 5 seconds
- **Backoff:** Exponential (5s, 10s, 20s)

### Error Types

**Retryable errors:**
- TimeoutException
- WebDriverException
- ConnectionError
- HTTPError

**Non-retryable errors:**
- ValidationError
- ValueError
- KeyError

### Error Logging

All errors are logged to the `scraping_logs` table with:
- Task ID
- URL
- Action
- Error message
- Timestamp

### Notifications

Task failures trigger notifications (logged to console by default):
- After all retries exhausted
- When error rate exceeds 20%

## Configuration

### Celery Settings

Located in `app/celery_app.py`:

```python
# Worker configuration
worker_concurrency=4          # Number of parallel workers
task_time_limit=300          # Task timeout (5 minutes)
task_soft_time_limit=270     # Soft timeout (4.5 minutes)

# Retry configuration
task_max_retries=3           # Maximum retry attempts
task_default_retry_delay=5   # Base retry delay
```

### Custom Configuration

Modify `app/config.py`:

```python
class Settings(BaseSettings):
    TASK_TIMEOUT: int = 300
    TASK_MAX_WORKERS: int = 4
    SCRAPING_MAX_RETRIES: int = 3
```

## Usage Examples

### Complete Workflow

```python
from app.database import SessionLocal
from app.models.task import Task
from app.repositories.task_repository import TaskRepository
from app.tasks import scrape_google_task

# Create task in database
db = SessionLocal()
task_repo = TaskRepository(db)

task = Task(
    keyword="SMA Internasional",
    city="Jakarta",
    target_platforms=["website", "facebook", "instagram"],
    max_results=50,
    status="pending"
)

created_task = task_repo.create(task)
db.close()

# Queue the scraping task
result = scrape_google_task.delay(str(created_task.id))

print(f"Task queued: {result.id}")
print(f"Status: {result.status}")
```

### Check Task Status

```python
from celery.result import AsyncResult
from app.celery_app import celery_app

# Get task result
result = AsyncResult("task-id-here", app=celery_app)

print(f"Status: {result.status}")
print(f"Result: {result.result}")
print(f"Traceback: {result.traceback}")
```

### Monitor Error Rate

```python
from app.database import SessionLocal
from app.tasks.error_handler import TaskErrorHandler

db = SessionLocal()
error_handler = TaskErrorHandler(db)

stats = error_handler.get_error_statistics("task-uuid")
print(f"Error rate: {stats['error_rate']}%")
print(f"Errors: {stats['error_count']}/{stats['total_operations']}")
print(f"Error types: {stats['error_types']}")

db.close()
```

## Testing

### Test Celery Setup

```bash
cd backend
python test_celery_setup.py
```

### Test Individual Task

```python
from app.tasks import extract_website_task

# Run synchronously for testing
result = extract_website_task.apply(
    args=["test-task-id", "https://example.com", "Test School"]
)

print(result.result)
```

## Troubleshooting

### Worker Not Starting

1. Check Redis is running:
   ```bash
   redis-cli ping
   ```

2. Check Celery configuration:
   ```bash
   celery -A app.celery_app inspect active
   ```

3. Check logs:
   ```bash
   celery -A app.celery_app worker --loglevel=debug
   ```

### Tasks Not Executing

1. Verify task is registered:
   ```python
   from app.celery_app import celery_app
   print(list(celery_app.tasks.keys()))
   ```

2. Check task queue:
   ```bash
   celery -A app.celery_app inspect active_queues
   ```

3. Check for errors:
   ```bash
   celery -A app.celery_app events
   ```

### High Error Rate

1. Check error statistics in database
2. Review scraping_logs table
3. Adjust retry configuration
4. Increase delays between requests

## Production Deployment

### Using Docker

```dockerfile
# Worker service in docker-compose.yml
worker:
  build: ./backend
  command: celery -A app.celery_app worker --loglevel=info
  environment:
    - DATABASE_URL=postgresql://user:pass@db:5432/recruitment
    - REDIS_URL=redis://redis:6379/0
  depends_on:
    - db
    - redis
```

### Scaling Workers

```bash
# Start multiple workers
celery -A app.celery_app worker --concurrency=8 --loglevel=info

# Or start multiple worker processes
celery multi start w1 w2 w3 -A app.celery_app --loglevel=info
```

### Monitoring

1. **Flower** - Web-based monitoring
2. **Prometheus** - Metrics collection
3. **Grafana** - Visualization
4. **Sentry** - Error tracking

## Best Practices

1. **Always use `.delay()` or `.apply_async()`** for async execution
2. **Keep tasks idempotent** - safe to retry
3. **Use task IDs** for tracking and debugging
4. **Monitor error rates** regularly
5. **Set appropriate timeouts** for long-running tasks
6. **Use task groups** for parallel execution
7. **Clean up resources** in finally blocks
8. **Log important events** for debugging

## References

- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Documentation](https://redis.io/documentation)
- [Task Queue Best Practices](https://docs.celeryproject.org/en/stable/userguide/tasks.html)
