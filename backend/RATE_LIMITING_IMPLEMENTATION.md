# Rate Limiting and Request Control Implementation

## Overview

This document describes the implementation of rate limiting and request control features for the Indonesia Recruitment Automation system. The implementation ensures that we don't overwhelm target websites and comply with requirement 7.5.

## Architecture

The rate limiting system consists of three main components:

### 1. Domain-Based Rate Limiter (`DomainRateLimiter`)

Controls request frequency to specific domains to prevent overwhelming individual websites.

**Features:**
- Per-domain request limits (default: 10 requests per 60 seconds)
- Minimum interval between requests to same domain (default: 2 seconds)
- Distributed mode using Redis for multi-worker coordination
- Local fallback mode when Redis is unavailable

**Configuration:**
```python
max_requests_per_domain = 10      # Max requests per domain in time window
time_window_seconds = 60          # Time window in seconds
min_request_interval = 2.0        # Minimum seconds between requests
```

### 2. Global Rate Limiter (`GlobalRateLimiter`)

Controls overall system request rate to prevent resource exhaustion.

**Features:**
- Global request limit (default: 60 requests per minute)
- Concurrent request limit (default: 10 concurrent requests)
- Distributed coordination via Redis
- Prevents system overload

**Configuration:**
```python
max_requests_per_minute = 60      # Max total requests per minute
max_concurrent_requests = 10      # Max concurrent requests
```

### 3. Task Priority Manager (`TaskThrottleManager`)

Manages Celery task priorities and throttling to ensure efficient resource allocation.

**Features:**
- Task-specific throttle limits
- Priority-based task execution
- Per-task concurrent and hourly limits
- Automatic task queuing when limits reached

**Task Priorities:**
```python
CRITICAL = 0    # Exports, user-initiated tasks
HIGH = 3        # New task initialization, Google searches
NORMAL = 5      # Regular scraping operations
LOW = 7         # Retry tasks, background jobs
BULK = 9        # Bulk operations, large exports
```

**Throttle Limits:**
```python
scrape_google_task:
  - max_concurrent: 2
  - max_per_hour: 20

extract_website_task:
  - max_concurrent: 5
  - max_per_hour: 100

extract_social_task:
  - max_concurrent: 3
  - max_per_hour: 50

export_data_task:
  - max_concurrent: 2
  - max_per_hour: 10
```

## Integration Points

### Scraping Engine

The `ScrapingEngine` class integrates rate limiting at the request level:

```python
engine = ScrapingEngine(
    headless=True,
    use_anti_detection=True,
    use_rate_limiting=True  # Enable rate limiting
)
```

When `fetch_page()` is called:
1. Rate limiter checks domain and global limits
2. Waits if necessary to comply with limits
3. Executes the request
4. Releases the request slot

### Celery Tasks

All scraping tasks now use the `PriorityTask` base class:

```python
@celery_app.task(
    bind=True,
    base=PriorityTask,
    name="scraping_tasks.scrape_google_task",
    priority=TaskPriority.HIGH
)
def scrape_google_task(self, task_id: str):
    # Task implementation
    pass
```

Task lifecycle:
1. `before_start()`: Check throttle limits, record task start
2. Task execution with rate-limited requests
3. `after_return()`: Record task end, release resources

### Celery Configuration

Priority support enabled in `celery_app.py`:

```python
celery_app.conf.update(
    task_inherit_parent_priority=True,
    task_default_priority=5,
    task_queue_max_priority=10,
    
    task_annotations={
        'scraping_tasks.scrape_google_task': {
            'rate_limit': '10/m',
        },
        'scraping_tasks.extract_website_task': {
            'rate_limit': '30/m',
        },
        'scraping_tasks.extract_social_task': {
            'rate_limit': '20/m',
        },
    },
)
```

## Configuration

All rate limiting settings are configurable via environment variables in `config.py`:

```python
# Rate Limiting
RATE_LIMIT_ENABLED: bool = True
RATE_LIMIT_MAX_REQUESTS_PER_DOMAIN: int = 10
RATE_LIMIT_DOMAIN_TIME_WINDOW: int = 60
RATE_LIMIT_MIN_REQUEST_INTERVAL: float = 2.0
RATE_LIMIT_MAX_REQUESTS_PER_MINUTE: int = 60
RATE_LIMIT_MAX_CONCURRENT_REQUESTS: int = 10

# Task Priority
TASK_PRIORITY_ENABLED: bool = True
```

Environment variables (`.env`):
```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_MAX_REQUESTS_PER_DOMAIN=10
RATE_LIMIT_DOMAIN_TIME_WINDOW=60
RATE_LIMIT_MIN_REQUEST_INTERVAL=2.0
RATE_LIMIT_MAX_REQUESTS_PER_MINUTE=60
RATE_LIMIT_MAX_CONCURRENT_REQUESTS=10
TASK_PRIORITY_ENABLED=true
```

## Usage Examples

### Basic Usage

```python
from app.utils.rate_limiter import get_rate_limit_manager

# Get rate limiter instance
rate_limiter = get_rate_limit_manager()

# Make a rate-limited request
url = "https://example.com"
if rate_limiter.wait_and_acquire(url):
    try:
        # Make your request
        response = fetch_page(url)
    finally:
        rate_limiter.release()
```

### Context Manager

```python
from app.utils.rate_limiter import RateLimitedRequestManager

with RateLimitedRequestManager() as rate_limiter:
    if rate_limiter.wait_and_acquire(url):
        # Request is automatically released on exit
        response = fetch_page(url)
```

### Task Priority

```python
from app.tasks.priority_manager import TaskPriority

# Queue task with specific priority
scrape_google_task.apply_async(
    args=[task_id],
    priority=TaskPriority.HIGH
)

# Export tasks automatically get CRITICAL priority
export_data_task.apply_async(
    args=[filename],
    kwargs=filters
)
```

### Check Throttle Status

```python
from app.tasks.priority_manager import get_throttle_manager

throttle_manager = get_throttle_manager()

# Get current stats for a task
stats = throttle_manager.get_task_stats('scraping_tasks.scrape_google_task')
print(f"Concurrent: {stats['concurrent']}, Hourly: {stats['hourly']}")
```

## Monitoring

### Logs

Rate limiting events are logged at appropriate levels:

```
INFO: Rate limit reached for example.com. Waiting 15.3s...
DEBUG: Waited 2.5s for domain rate limit
WARNING: Task scraping_tasks.scrape_google_task blocked: concurrent limit (2) reached
```

### Redis Keys

When using distributed mode, the following Redis keys are used:

**Domain Rate Limiting:**
- `rate_limit:requests:{domain}` - Sorted set of request timestamps
- `rate_limit:last:{domain}` - Last request timestamp

**Global Rate Limiting:**
- `rate_limit:global:requests` - Sorted set of all request timestamps
- `rate_limit:global:concurrent` - Current concurrent request count

**Task Throttling:**
- `throttle:concurrent:{task_name}` - Current concurrent task count
- `throttle:hourly:{task_name}` - Hourly task count

### Monitoring Commands

```bash
# Check domain rate limits
redis-cli ZCARD rate_limit:requests:example.com

# Check global concurrent requests
redis-cli GET rate_limit:global:concurrent

# Check task throttle status
redis-cli GET throttle:concurrent:scraping_tasks.scrape_google_task
redis-cli GET throttle:hourly:scraping_tasks.scrape_google_task
```

## Benefits

1. **Website Protection**: Prevents overwhelming target websites with too many requests
2. **Resource Management**: Controls system resource usage through concurrent limits
3. **Priority Handling**: Ensures critical tasks (exports) execute before background tasks
4. **Distributed Coordination**: Multiple workers coordinate via Redis
5. **Graceful Degradation**: Falls back to local mode if Redis unavailable
6. **Compliance**: Helps comply with robots.txt and rate limiting policies
7. **Scalability**: Supports horizontal scaling with distributed rate limiting

## Testing

To test rate limiting:

```python
# Test domain rate limiter
from app.utils.rate_limiter import DomainRateLimiter

limiter = DomainRateLimiter(max_requests_per_domain=5, time_window_seconds=10)

# Make rapid requests - should see delays
for i in range(10):
    wait_time = limiter.wait_if_needed("https://example.com")
    print(f"Request {i+1}: waited {wait_time:.2f}s")
```

```python
# Test task throttling
from app.tasks.priority_manager import get_throttle_manager

throttle = get_throttle_manager()

# Check if task can execute
can_run = throttle.can_execute_task('scraping_tasks.scrape_google_task')
print(f"Can execute: {can_run}")
```

## Troubleshooting

### Issue: Tasks not respecting priorities

**Solution**: Ensure Redis is running and Celery workers are started with priority support:
```bash
celery -A app.celery_app worker --loglevel=info -O fair
```

### Issue: Rate limiting too aggressive

**Solution**: Adjust limits in configuration:
```python
RATE_LIMIT_MAX_REQUESTS_PER_DOMAIN=20  # Increase from 10
RATE_LIMIT_DOMAIN_TIME_WINDOW=120      # Increase window to 2 minutes
```

### Issue: Redis connection errors

**Solution**: System automatically falls back to local mode. Check Redis connection:
```bash
redis-cli ping
```

## Future Enhancements

1. **Adaptive Rate Limiting**: Automatically adjust limits based on response times
2. **Per-Website Configuration**: Custom limits for specific domains
3. **Metrics Dashboard**: Real-time visualization of rate limiting stats
4. **Alert System**: Notifications when limits are frequently hit
5. **Machine Learning**: Predict optimal rate limits based on historical data

## Related Files

- `backend/app/utils/rate_limiter.py` - Rate limiting implementation
- `backend/app/tasks/priority_manager.py` - Task priority management
- `backend/app/scraper/scraping_engine.py` - Integration with scraping engine
- `backend/app/tasks/scraping_tasks.py` - Task implementations
- `backend/app/celery_app.py` - Celery configuration
- `backend/app/config.py` - Configuration settings
