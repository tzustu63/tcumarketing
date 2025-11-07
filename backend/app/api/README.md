# REST API Implementation

## Overview

This directory contains the complete REST API implementation for the Tzu Chi University Recruitment Automation System (慈濟大學招生通路自動開發系統).

## Structure

```
app/api/
├── __init__.py           # API package initialization
├── dependencies.py       # Dependency injection (database sessions)
├── schemas.py           # Pydantic models for request/response validation
├── README.md            # This file
└── routes/
    ├── __init__.py      # Routes package initialization
    ├── tasks.py         # Task management endpoints
    ├── contacts.py      # Contact information query endpoints
    └── stats.py         # Statistics and logging endpoints
```

## API Endpoints

### Task Management (`/api/tasks`)

- **POST /api/tasks** - Create a new search task
- **GET /api/tasks** - Get list of tasks (with filtering and pagination)
- **GET /api/tasks/{id}** - Get task details
- **POST /api/tasks/{id}/start** - Start a pending task
- **DELETE /api/tasks/{id}** - Delete a task
- **GET /api/tasks/{id}/progress** - Get task progress

### Contact Information (`/api/contacts`)

- **GET /api/contacts** - Query contacts (with filtering and pagination)
- **GET /api/contacts/{id}** - Get single contact details
- **GET /api/contacts/task/{task_id}** - Get contacts by task
- **GET /api/contacts/stats/summary** - Get contact statistics summary

### Statistics & Logs (`/api`)

- **GET /api/stats** - Get system-wide statistics
- **GET /api/logs** - Get scraping logs (with filtering)
- **GET /api/logs/task/{task_id}** - Get logs for specific task
- **GET /api/logs/errors** - Get error logs only
- **GET /api/stats/task/{task_id}** - Get statistics for specific task

## Features

### Request Validation
All API requests are validated using Pydantic models with:
- Type checking
- Field validation
- Custom validators
- Clear error messages

### Response Models
Consistent response formats using Pydantic schemas:
- Type-safe responses
- Automatic documentation
- JSON serialization

### Error Handling
- HTTP exception handling
- Validation error responses
- Custom error messages
- Proper status codes

### Filtering & Pagination
- Query parameter filtering
- Offset-based pagination
- Configurable page sizes
- Total count in responses

### CORS Support
- Configured for frontend integration
- Customizable allowed origins
- Credential support

## Usage Examples

### Create a Task

```bash
curl -X POST "http://localhost:8000/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "SMA Internasional",
    "city": "Jakarta",
    "target_platforms": ["website", "facebook"],
    "max_results": 100
  }'
```

### Get Tasks

```bash
curl "http://localhost:8000/api/tasks?status=completed&skip=0&limit=10"
```

### Start a Task

```bash
curl -X POST "http://localhost:8000/api/tasks/{task_id}/start"
```

### Query Contacts

```bash
curl "http://localhost:8000/api/contacts?institution_type=高中&has_email=true&skip=0&limit=50"
```

### Get Statistics

```bash
curl "http://localhost:8000/api/stats"
```

## Running the API

### Development Mode

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Docker

```bash
docker-compose up api
```

## API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

## Configuration

API configuration is managed through environment variables in `.env`:

```env
# API Settings
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# CORS Settings
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/recruitment

# Redis
REDIS_URL=redis://localhost:6379/0
```

## Dependencies

The API requires the following Python packages:
- fastapi
- uvicorn
- pydantic
- sqlalchemy
- psycopg2-binary
- python-multipart

## Testing

To test the API implementation:

```bash
cd backend
python test_api_import.py
```

## Integration with Celery

The API integrates with Celery for asynchronous task execution:
- Tasks are queued when started via `/api/tasks/{id}/start`
- Progress updates are stored in the database
- Results are accessible through the API

## Security Considerations

- Input validation on all endpoints
- SQL injection prevention via SQLAlchemy ORM
- CORS configuration for frontend access
- Rate limiting (to be implemented)
- Authentication (to be implemented)

## Next Steps

Future enhancements:
- JWT authentication
- API rate limiting
- WebSocket support for real-time updates
- Export functionality endpoints
- Batch operations
- Advanced search capabilities
