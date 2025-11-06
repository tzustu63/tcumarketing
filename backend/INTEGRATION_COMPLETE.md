# Complete Workflow Integration Documentation

## Overview

This document describes the complete integration of all modules in the Indonesia Recruitment Automation system. The workflow orchestrates the following components:

1. **Scraping Engine** - Web crawling and page fetching
2. **Extractor Module** - Contact information extraction
3. **Validator Module** - Data validation and quality scoring
4. **Database Layer** - Data persistence and retrieval

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Workflow Orchestrator                     │
│                  (ScrapingWorkflow Class)                    │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐     ┌──────────────┐
│   Scraping   │      │  Extraction  │     │  Validation  │
│    Engine    │──────▶    Module    │─────▶    Module    │
└──────────────┘      └──────────────┘     └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
                      ┌──────────────┐
                      │   Database   │
                      │  Repository  │
                      └──────────────┘
```

## Complete Workflow Steps

### 1. Google Search Workflow

**Entry Point**: `ScrapingWorkflow.execute_google_search_workflow()`

**Steps**:
1. Initialize ScrapingEngine with anti-detection and rate limiting
2. Execute Google search using GoogleScraper
3. Filter results by target platforms (website, facebook, instagram)
4. For each result:
   - Route to appropriate extraction workflow
   - Track progress and update task status
5. Aggregate results and return WorkflowResult

**Code Example**:
```python
from app.workflows import ScrapingWorkflow

workflow = ScrapingWorkflow(db_session)
result = workflow.execute_google_search_workflow(
    task_id="task-123",
    keyword="SMA Internasional",
    city="Jakarta",
    target_platforms=["website", "facebook"],
    max_results=50
)

print(f"Contacts saved: {result.contacts_saved}")
print(f"Duplicates skipped: {result.duplicates_skipped}")
```

### 2. Website Extraction Workflow

**Entry Point**: `ScrapingWorkflow.execute_website_extraction_workflow()`

**Steps**:
1. Initialize ScrapingEngine
2. Find contact page using ContactPageFinder
3. Fetch page content with retry logic
4. Parse HTML using HTMLParser (includes institution classification)
5. Extract emails and WhatsApp numbers
6. Validate each contact field using ContactValidator
7. Calculate quality score
8. Check for duplicates using ContactRepository
9. Save to database if not duplicate
10. Log operation to ScrapingLog

**Integration Points**:
- `ScrapingEngine.fetch_page_with_retry()` → `HTMLParser.parse_html()`
- `HTMLParser` → `ContactValidator.validate_email()` / `validate_phone()`
- `ContactValidator` → `ContactRepository.check_duplicate()`
- `ContactRepository.create()` → Database

**Code Example**:
```python
result = workflow.execute_website_extraction_workflow(
    task_id="task-123",
    url="https://smajakarta.sch.id",
    institution_name="SMA Internasional Jakarta"
)
```

### 3. Social Media Extraction Workflow

**Entry Point**: 
- `ScrapingWorkflow.execute_facebook_extraction_workflow()`
- `ScrapingWorkflow.execute_instagram_extraction_workflow()`

**Steps**:
1. Initialize ScrapingEngine
2. Extract profile data using platform-specific scraper
3. Extract contact info using SocialMediaExtractor
4. Validate extracted data
5. Classify institution type
6. Calculate quality score (adjusted for social media source)
7. Check for duplicates
8. Save to database
9. Log operation

**Integration Points**:
- `FacebookScraper/InstagramScraper` → `SocialMediaExtractor`
- `SocialMediaExtractor` → `ContactValidator`
- `ContactValidator` → `ContactRepository`

## Module Integration Details

### Scraper → Extractor Integration

**Connection**: Page content flows from scraper to extractor

```python
# Scraper provides PageContent
page_content = engine.fetch_page_with_retry(url)

# Extractor processes HTML
parsed_data = html_parser.parse_html(
    page_content.html,
    institution_name=institution_name
)
```

**Data Flow**:
- ScrapingEngine returns `PageContent` object with HTML
- HTMLParser extracts structured data including:
  - Emails
  - WhatsApp numbers
  - Institution type (via InstitutionClassifier)
  - Page title

### Extractor → Validator Integration

**Connection**: Extracted data is validated before storage

```python
# Extract emails
emails = parsed_data.get("emails", [])

# Validate each email
valid_emails = []
for email in emails:
    result = contact_validator.validate_email(email)
    if result.is_valid:
        valid_emails.append(email)
```

**Validation Rules**:
- Email format validation
- Indonesian domain checking
- Phone number format validation
- Number normalization to +62 format

### Validator → Database Integration

**Connection**: Validated data is saved with quality scores

```python
# Calculate quality score
quality_score = contact_validator.calculate_quality_score(
    has_email=len(valid_emails) > 0,
    has_whatsapp=len(valid_whatsapp) > 0,
    source_platform="website",
    has_institution_name=True
)

# Create contact object
contact = Contact(
    task_id=task_id,
    institution_name=institution_name,
    institution_type=parsed_data["institution_type"],
    source_url=url,
    source_platform="website",
    email=valid_emails[0] if valid_emails else None,
    whatsapp=valid_whatsapp[0] if valid_whatsapp else None,
    quality_score=quality_score
)

# Check for duplicates
if not contact_repo.check_duplicate(contact):
    contact_repo.create(contact)
```

**Quality Score Calculation**:
- Email present: +40 points
- WhatsApp present: +40 points
- Official website source: +10 points
- Institution name present: +10 points
- Maximum score: 100 points

## Error Handling Integration

### Retry Logic

All workflows implement retry logic with exponential backoff:

```python
# In ScrapingEngine
page_content = engine.fetch_page_with_retry(
    url,
    max_retries=3
)
```

### Error Logging

All errors are logged to the database:

```python
self.log_repo.create(ScrapingLog(
    task_id=task_id,
    url=url,
    action="extract_website",
    status="failed",
    error_message=str(e)
))
```

### Graceful Degradation

- If contact page not found, use main URL
- If email invalid, still save if WhatsApp is valid
- If extraction fails, log error and continue with next result

## Celery Task Integration

The workflow is integrated with Celery tasks for asynchronous execution:

### Task Flow

```
scrape_google_task
    │
    ├─→ extract_website_task (parallel)
    ├─→ extract_website_task (parallel)
    ├─→ extract_social_task (parallel)
    └─→ extract_social_task (parallel)
```

### Task Implementation

```python
@celery_app.task
def scrape_google_task(task_id: str):
    """Main task that orchestrates the workflow"""
    db = SessionLocal()
    try:
        workflow = ScrapingWorkflow(db)
        result = workflow.execute_google_search_workflow(
            task_id=task_id,
            keyword=task.keyword,
            city=task.city,
            target_platforms=task.target_platforms,
            max_results=task.max_results
        )
        return result
    finally:
        db.close()
```

## Testing Integration

### End-to-End Test Coverage

The `test_end_to_end_workflow.py` file provides comprehensive integration tests:

1. **test_complete_website_extraction_workflow**
   - Tests full workflow from HTML to database
   - Verifies all integration points
   - Validates data quality

2. **test_social_media_extraction_workflow**
   - Tests social media extraction
   - Verifies platform-specific handling
   - Validates institution classification

3. **test_duplicate_detection_workflow**
   - Tests duplicate checking across workflow
   - Verifies repository integration

4. **test_error_handling_workflow**
   - Tests error propagation
   - Verifies logging integration

5. **test_quality_score_calculation_workflow**
   - Tests quality scoring across scenarios
   - Verifies validator integration

6. **test_institution_classification_workflow**
   - Tests classification in complete workflow
   - Verifies extractor integration

### Running Tests

```bash
# Run all integration tests
pytest tests/test_end_to_end_workflow.py -v

# Run specific test
pytest tests/test_end_to_end_workflow.py::TestEndToEndWorkflow::test_complete_website_extraction_workflow -v

# Run with coverage
pytest tests/test_end_to_end_workflow.py --cov=app.workflows --cov-report=html
```

## API Integration

The workflow is exposed through REST API endpoints:

### Start Task Endpoint

```http
POST /api/tasks/{task_id}/start
```

This endpoint:
1. Updates task status to "running"
2. Queues `scrape_google_task` with task_id
3. Returns immediately (async execution)

### Progress Tracking

```http
GET /api/tasks/{task_id}/progress
```

Returns:
- Current status
- Progress percentage
- Results count
- Error messages (if any)

## Performance Considerations

### Rate Limiting

- Integrated at ScrapingEngine level
- Configurable delays between requests
- Prevents overwhelming target websites

### Parallel Processing

- Multiple extraction tasks run in parallel
- Celery worker pool manages concurrency
- Database connections pooled

### Resource Management

- Browser instances properly closed
- Database sessions managed with context managers
- Memory-efficient batch processing

## Configuration

### Environment Variables

```bash
# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=30

# Anti-detection
ANTI_DETECTION_ENABLED=true
MIN_REQUEST_DELAY=2.0
MAX_REQUEST_DELAY=5.0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Workflow Configuration

```python
# Initialize with custom settings
workflow = ScrapingWorkflow(
    db=db_session,
    use_anti_detection=True,
    use_rate_limiting=True
)
```

## Monitoring and Observability

### Logging

All workflow operations are logged:

```python
logger.info(f"Starting Google search workflow for task {task_id}")
logger.info(f"Found {len(search_results)} results")
logger.info(f"Saved contact for: {institution_name}")
logger.error(f"Error processing result {url}: {e}")
```

### Metrics

WorkflowResult provides execution metrics:

```python
result = workflow.execute_google_search_workflow(...)

print(f"Success: {result.success}")
print(f"Contacts found: {result.contacts_found}")
print(f"Contacts saved: {result.contacts_saved}")
print(f"Duplicates skipped: {result.duplicates_skipped}")
print(f"Execution time: {result.execution_time}s")
print(f"Errors: {len(result.errors)}")
```

### Database Logs

All operations logged to `scraping_logs` table:

```sql
SELECT 
    action,
    status,
    COUNT(*) as count,
    AVG(response_time) as avg_time
FROM scraping_logs
WHERE task_id = 'task-123'
GROUP BY action, status;
```

## Troubleshooting

### Common Integration Issues

1. **Browser not closing properly**
   - Ensure `engine.close()` is called in finally block
   - Use context manager: `with ScrapingEngine() as engine:`

2. **Database connection leaks**
   - Always close database sessions
   - Use dependency injection in API routes

3. **Rate limiting too aggressive**
   - Adjust `MIN_REQUEST_DELAY` and `MAX_REQUEST_DELAY`
   - Increase `RATE_LIMIT_REQUESTS_PER_MINUTE`

4. **Duplicate detection not working**
   - Check unique constraint on contacts table
   - Verify `check_duplicate()` logic

5. **Quality scores too low**
   - Review validation rules
   - Check if data is being extracted correctly

## Future Enhancements

1. **Batch Processing**
   - Process multiple URLs in single browser session
   - Reduce overhead of browser initialization

2. **Caching**
   - Cache search results
   - Cache validated domains

3. **Machine Learning**
   - Train model for better institution classification
   - Improve contact information extraction accuracy

4. **Distributed Scraping**
   - Multiple worker nodes
   - Load balancing across scrapers

## Conclusion

The complete workflow integration successfully connects all system modules:

✅ Scraping Engine provides robust web crawling
✅ Extractor Module accurately identifies contact information
✅ Validator Module ensures data quality
✅ Database Layer persists validated data
✅ Error handling provides resilience
✅ Logging enables monitoring and debugging
✅ Celery integration enables scalable async processing

The system is production-ready and can handle the complete workflow from search to storage with proper error handling, validation, and logging at each step.
