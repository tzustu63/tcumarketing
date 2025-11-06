# Celery Task Queue - Quick Start Guide

## Prerequisites

1. Redis running on port 6379
2. PostgreSQL database set up
3. Python dependencies installed

## Start Services

### 1. Start Redis (if not running)

```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or using Docker Compose
docker-compose up -d redis
```

### 2. Start Celery Worker

```bash
cd backend
celery -A app.celery_app worker --loglevel=info --concurrency=4
```

You should see output like:
```
 -------------- celery@hostname v5.3.6
---- **** -----
--- * ***  * -- Darwin-23.0.0-arm64-arm-64bit 2024-01-03 10:00:00
-- * - **** ---
- ** ---------- [config]
- ** ---------- .> app:         recruitment_tasks:0x...
- ** ---------- .> transport:   redis://localhost:6379/0
- ** ---------- .> results:     redis://localhost:6379/0
- *** --- * --- .> concurrency: 4 (prefork)
-- ******* ---- .> task events: OFF
--- ***** -----
 -------------- [queues]
                .> celery           exchange=celery(direct) key=celery

[tasks]
  . scraping_tasks.extract_social_task
  . scraping_tasks.extract_website_task
  . scraping_tasks.scrape_google_task
```

## Test the Setup

### Option 1: Run Verification Script

```bash
cd backend
python test_celery_setup.py
```

### Option 2: Queue a Test Task

```python
# In Python shell or script
from app.database import SessionLocal
from app.models.task import Task
from app.repositories.task_repository import TaskRepository
from app.tasks import scrape_google_task

# Create a test task
db = SessionLocal()
task_repo = TaskRepository(db)

task = Task(
    keyword="SMA Internasional",
    city="Jakarta",
    target_platforms=["website"],
    max_results=10,
    status="pending"
)

created_task = task_repo.create(task)
task_id = str(created_task.id)
db.close()

# Queue the task
result = scrape_google_task.delay(task_id)

print(f"Task queued: {result.id}")
print(f"Check worker logs for execution")
```

## Monitor Tasks

### Option 1: Check Worker Logs

Watch the Celery worker terminal for task execution logs.

### Option 2: Use Flower (Web UI)

```bash
# Install flower (if not installed)
pip install flower

# Start Flower
celery -A app.celery_app flower --port=5555
```

Open browser: http://localhost:5555

### Option 3: Check Database

```sql
-- Check task status
SELECT id, keyword, city, status, progress, results_count 
FROM tasks 
ORDER BY created_at DESC 
LIMIT 10;

-- Check scraping logs
SELECT task_id, url, action, status, error_message, created_at
FROM scraping_logs
ORDER BY created_at DESC
LIMIT 20;

-- Check extracted contacts
SELECT institution_name, email, whatsapp, source_platform, quality_score
FROM contacts
ORDER BY extracted_at DESC
LIMIT 10;
```

## Common Commands

### Start Worker (Development)

```bash
# With auto-reload on code changes
watchmedo auto-restart --directory=./app --pattern=*.py --recursive -- \
  celery -A app.celery_app worker --loglevel=info
```

### Start Worker (Production)

```bash
# With more workers
celery -A app.celery_app worker --loglevel=info --concurrency=8

# Multiple worker processes
celery multi start w1 w2 w3 -A app.celery_app --loglevel=info
```

### Stop Workers

```bash
# Stop all workers
celery multi stop w1 w2 w3

# Or Ctrl+C in the worker terminal
```

### Inspect Workers

```bash
# Check active tasks
celery -A app.celery_app inspect active

# Check registered tasks
celery -A app.celery_app inspect registered

# Check worker stats
celery -A app.celery_app inspect stats
```

### Purge Queue

```bash
# Remove all pending tasks
celery -A app.celery_app purge
```

## Troubleshooting

### Worker Won't Start

1. **Check Redis:**
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

2. **Check Python path:**
   ```bash
   cd backend
   python -c "from app.celery_app import celery_app; print('OK')"
   ```

3. **Check dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Tasks Not Executing

1. **Verify task is registered:**
   ```bash
   celery -A app.celery_app inspect registered
   ```

2. **Check for errors in worker logs**

3. **Verify database connection:**
   ```python
   from app.database import SessionLocal
   db = SessionLocal()
   print("Database connected")
   db.close()
   ```

### High Error Rate

1. Check `scraping_logs` table for error patterns
2. Increase delays in `app/config.py`:
   ```python
   SCRAPING_MIN_DELAY: int = 5
   SCRAPING_MAX_DELAY: int = 10
   ```
3. Reduce concurrency:
   ```bash
   celery -A app.celery_app worker --concurrency=2
   ```

## Environment Variables

Create `.env` file in backend directory:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/recruitment

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Task Configuration
TASK_TIMEOUT=300
TASK_MAX_WORKERS=4

# Scraping Configuration
SCRAPING_HEADLESS=True
SCRAPING_MAX_RETRIES=3
SCRAPING_MIN_DELAY=2
SCRAPING_MAX_DELAY=5
```

## Docker Deployment

Add to `docker-compose.yml`:

```yaml
services:
  worker:
    build: ./backend
    command: celery -A app.celery_app worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/recruitment
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - db
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
```

Start with:
```bash
docker-compose up -d worker
```

## Next Steps

1. ✅ Task queue system is ready
2. ⏭️ Implement REST API (Task 7) to create and manage tasks
3. ⏭️ Implement frontend UI (Task 9) to interact with the system

## Documentation

- Full documentation: `backend/app/tasks/README.md`
- Implementation details: `backend/app/tasks/IMPLEMENTATION_SUMMARY.md`
- Celery docs: https://docs.celeryproject.org/
