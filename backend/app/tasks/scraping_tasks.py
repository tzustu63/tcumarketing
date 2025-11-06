"""
Celery Tasks for Web Scraping and Data Extraction
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from celery import Task
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.task import Task as TaskModel
from app.models.contact import Contact
from app.models.scraping_log import ScrapingLog
from app.repositories.task_repository import TaskRepository
from app.repositories.contact_repository import ContactRepository
from app.repositories.scraping_log_repository import ScrapingLogRepository
from app.scraper.scraping_engine import ScrapingEngine
from app.scraper.google_scraper import GoogleScraper, SearchResult
from app.scraper.duckduckgo_scraper import DuckDuckGoScraper
from app.scraper.google_api_scraper import GoogleAPISearcher
from app.scraper.contact_page_finder import ContactPageFinder
from app.extractor.contact_extractor import ContactExtractor
from app.extractor.contact_validator import ContactValidator
from app.extractor.html_parser import HTMLParser
from app.tasks.error_handler import TaskErrorHandler, RetryStrategy
from app.tasks.priority_manager import PriorityTask, TaskPriority, get_throttle_manager
from app.services.export_service import ExportService
from app.config import settings

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task with database session management"""
    _db: Optional[Session] = None
    
    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    def after_return(self, *args, **kwargs):
        """Clean up database session after task completion"""
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(
    bind=True,
    base=PriorityTask,
    name="scraping_tasks.scrape_google_task",
    max_retries=3,
    default_retry_delay=5,
    priority=TaskPriority.HIGH
)
def scrape_google_task(self, task_id: str) -> Dict[str, Any]:
    """
    Celery task to scrape Google search results.
    
    Args:
        task_id: UUID of the task in database
        
    Returns:
        Dictionary with task results
    """
    logger.info(f"Starting Google scrape task for task_id: {task_id}")
    
    # Get database session
    db = SessionLocal()
    task_repo = TaskRepository(db)
    log_repo = ScrapingLogRepository(db)
    
    # Get task from database
    task = task_repo.get(task_id)
    if not task:
        logger.error(f"Task {task_id} not found")
        return {"status": "error", "message": "Task not found"}
    
    # Update task status
    task.status = "running"
    task.started_at = datetime.utcnow()
    task.progress = 0
    db.commit()
    
    engine = None
    try:
        # Initialize scraping engine with rate limiting
        engine = ScrapingEngine(
            headless=True,
            use_anti_detection=True,
            use_rate_limiting=settings.RATE_LIMIT_ENABLED
        )
        
        # Build search query
        query = f"{task.keyword} {task.city}"
        country_code = getattr(task, 'country', 'ID')  # Default to Indonesia
        
        # Try Google Custom Search API first (if configured)
        search_results = []
        use_api = False
        api_available = bool(settings.GOOGLE_API_KEY and settings.GOOGLE_CSE_ID)
        
        if api_available:
            try:
                logger.info(f"🔍 Using Google Custom Search API ({country_code}) for: {query}")
                api_searcher = GoogleAPISearcher()
                search_results = api_searcher.search(
                    query=query,
                    max_results=task.max_results,
                    country_code=country_code
                )
                use_api = True
                logger.info(f"✅ Google API returned {len(search_results)} results")
                
                # If API returns 0 results, it's still a valid response (no fallback needed)
                if len(search_results) == 0:
                    logger.info(f"ℹ️ No results found for query: {query}")
                    
            except Exception as e:
                logger.error(f"❌ Google API search failed: {e}")
                logger.info(f"📝 Falling back to web scraping method")
                use_api = False
                search_results = []
        else:
            logger.warning(f"⚠️ Google API not configured (API Key or CSE ID missing)")
            logger.info(f"📝 Using web scraping method")
        
        # Fallback to web scraping only if API failed (not if it returned 0 results)
        if not use_api and not search_results:
            logger.info(f"Using web scraping for Google ({country_code}): {query}")
            google_scraper = GoogleScraper(engine, country_code=country_code)
            max_pages = min(10, (task.max_results // 10) + 1)
            search_results = google_scraper.search_google(query, max_pages=max_pages)
            logger.info(f"Found {len(search_results)} results from web scraping")
        
        # Update progress
        task.progress = 10
        db.commit()
        
        # Update progress
        task.progress = 50
        db.commit()
        
        # Filter results by target platforms
        filtered_results = []
        for result in search_results:
            if result.platform in task.target_platforms or "website" in task.target_platforms:
                filtered_results.append(result)
                
                # Log each result
                log_repo.create({
                    "task_id": task.id,
                    "url": result.url,
                    "action": "google_search",
                    "status": "success",
                    "response_time": 0
                })
        
        logger.info(f"Filtered to {len(filtered_results)} results matching target platforms")
        
        # Update progress
        task.progress = 70
        db.commit()
        
        # Queue extraction tasks for each result
        extraction_tasks = []
        for result in filtered_results[:task.max_results]:
            # Only extract from websites, skip social media platforms
            if result.platform not in ["facebook", "instagram"]:
                extraction_tasks.append(
                    extract_website_task.s(task_id, result.url, result.title)
                )
        
        # Execute extraction tasks
        from celery import group, chord
        
        if extraction_tasks:
            # Use chord to wait for all extraction tasks to complete
            # Progress: 70% (search done) -> 100% (all extractions done)
            task.progress = 70
            db.commit()
            
            logger.info(f"Queued {len(extraction_tasks)} extraction tasks")
            
            # Create a callback task to mark as completed
            job = chord(extraction_tasks)(
                mark_task_completed.s(task_id, len(extraction_tasks))
            )
            
            logger.info(f"Google scrape task queued extraction tasks for task_id: {task_id}")
        else:
            # No extraction tasks, mark as completed immediately
            task.progress = 100
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Google scrape task completed (no results) for task_id: {task_id}")
        
        return {
            "status": "success",
            "task_id": task_id,
            "results_count": len(filtered_results),
            "extraction_tasks_queued": len(extraction_tasks)
        }
        
    except Exception as e:
        logger.error(f"Error in Google scrape task: {e}", exc_info=True)
        
        # Use error handler
        error_handler = TaskErrorHandler(db)
        error_handler.log_error(
            task_id=task_id,
            url=f"google_search:{task.keyword}",
            action="google_search",
            error=e,
            retry_count=self.request.retries,
            max_retries=self.max_retries
        )
        
        # Update task status
        task.status = "failed"
        task.error_message = str(e)
        task.completed_at = datetime.utcnow()
        db.commit()
        
        # Check if should retry
        if error_handler.should_retry(e, self.request.retries, self.max_retries):
            retry_delay = RetryStrategy.calculate_delay(e, self.request.retries)
            logger.info(f"Retrying task in {retry_delay} seconds")
            raise self.retry(exc=e, countdown=retry_delay)
        else:
            # Send failure notification
            error_handler.notify_task_failure(
                task_id=task_id,
                task_name=self.name,
                error=e,
                retry_count=self.request.retries
            )
            raise
        
    finally:
        if engine:
            engine.close()
        db.close()


def _update_extraction_progress(db: Session, task_id: str):
    """
    Update task progress based on completed extraction tasks.
    Progress range: 70% (search done) -> 95% (extractions in progress)
    Final 100% is set by mark_task_completed callback.
    """
    try:
        from app.celery_app import celery_app as app
        
        # Get task from database
        task_repo = TaskRepository(db)
        task = task_repo.get(task_id)
        
        if not task:
            return
        
        # Get active extraction tasks for this task_id
        inspect = app.control.inspect()
        active_tasks = inspect.active()
        
        if not active_tasks:
            return
        
        # Count extraction tasks for this task_id
        extraction_count = 0
        for worker, tasks in active_tasks.items():
            for t in tasks:
                if t['name'] == 'scraping_tasks.extract_website_task':
                    if t['args'] and len(t['args']) > 0 and t['args'][0] == task_id:
                        extraction_count += 1
        
        # Calculate progress: 70% base + up to 25% for extractions
        # If there are still active tasks, keep progress below 95%
        if extraction_count > 0:
            # Still have active tasks, keep progress between 70-95%
            max_progress = 95
            current_progress = min(max_progress, task.progress)
            task.progress = current_progress
        
        db.commit()
        
    except Exception as e:
        logger.debug(f"Error updating extraction progress: {e}")
        # Don't fail the task if progress update fails


@celery_app.task(
    name="scraping_tasks.mark_task_completed"
)
def mark_task_completed(results, task_id: str, total_tasks: int) -> Dict[str, Any]:
    """
    Callback task to mark the main task as completed after all extraction tasks finish.
    
    Args:
        results: Results from all extraction tasks
        task_id: UUID of the main task
        total_tasks: Total number of extraction tasks
        
    Returns:
        Dictionary with completion status
    """
    logger.info(f"All extraction tasks completed for task_id: {task_id}")
    
    db = SessionLocal()
    task_repo = TaskRepository(db)
    
    try:
        task = task_repo.get(task_id)
        if task:
            task.progress = 100
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Task {task_id} marked as completed with {task.results_count} results")
            
            return {
                "status": "success",
                "task_id": task_id,
                "total_tasks": total_tasks,
                "results_count": task.results_count
            }
    except Exception as e:
        logger.error(f"Error marking task as completed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(
    bind=True,
    base=PriorityTask,
    name="scraping_tasks.extract_website_task",
    max_retries=3,
    default_retry_delay=5,
    priority=TaskPriority.NORMAL
)
def extract_website_task(
    self,
    task_id: str,
    url: str,
    institution_name: str = ""
) -> Dict[str, Any]:
    """
    Celery task to extract contact information from a website.
    
    Args:
        task_id: UUID of the parent task
        url: Website URL to extract from
        institution_name: Name of the institution
        
    Returns:
        Dictionary with extraction results
    """
    logger.info(f"Starting website extraction for: {url}")
    
    # Get database session
    db = SessionLocal()
    task_repo = TaskRepository(db)
    contact_repo = ContactRepository(db)
    log_repo = ScrapingLogRepository(db)
    
    engine = None
    try:
        # Initialize components with rate limiting
        engine = ScrapingEngine(
            headless=True,
            use_anti_detection=True,
            use_rate_limiting=settings.RATE_LIMIT_ENABLED
        )
        contact_finder = ContactPageFinder(engine)
        contact_extractor = ContactExtractor()
        contact_validator = ContactValidator()
        html_parser = HTMLParser()
        
        # Find contact page
        contact_url = contact_finder.find_contact_page(url)
        if not contact_url:
            contact_url = url
            logger.info(f"No specific contact page found, using main URL: {url}")
        else:
            logger.info(f"Found contact page: {contact_url}")
        
        # Fetch page content
        page_content = engine.fetch_page_with_retry(contact_url)
        
        # Parse HTML and extract contact info (includes classification)
        parsed_data = html_parser.parse_html(
            page_content.html, 
            institution_name=institution_name
        )
        
        # Validate contact information
        emails = []
        for email in parsed_data.get("emails", []):
            if contact_validator.validate_email(email):
                emails.append(email)
        
        whatsapp_numbers = []
        for number in parsed_data.get("whatsapp_numbers", []):
            if contact_validator.validate_phone(number):
                whatsapp_numbers.append(number)
        
        # Get institution type from parsed data
        institution_type = parsed_data.get("institution_type")
        
        # Calculate quality score
        quality_score = contact_validator.calculate_quality_score(
            has_email=len(emails) > 0,
            has_whatsapp=len(whatsapp_numbers) > 0,
            source_platform="website"
        )
        
        # Get task to retrieve country code and keyword
        task = task_repo.get(task_id)
        country_code = task.country if task else "ID"
        keyword = task.keyword if task else None
        
        # Save to database if contact info found
        if emails or whatsapp_numbers:
            contact_data = {
                "task_id": task_id,
                "country": country_code,
                "keyword": keyword,
                "institution_name": institution_name or parsed_data.get("title", "Unknown"),
                "institution_type": institution_type,
                "source_url": url,
                "source_platform": "website",
                "email": emails[0] if emails else None,
                "whatsapp": whatsapp_numbers[0] if whatsapp_numbers else None,
                "additional_info": {
                    "all_emails": emails,
                    "all_whatsapp": whatsapp_numbers,
                    "contact_page_url": contact_url
                },
                "quality_score": quality_score
            }
            
            # Check for duplicates
            if not contact_repo.check_duplicate_dict(contact_data):
                contact_repo.create(contact_data)
                task_repo.increment_results_count(task_id)
                logger.info(f"Saved contact for: {institution_name}")
            else:
                logger.info(f"Duplicate contact found, skipping: {url}")
        
        # Update task progress (incremental)
        # This will be called by each extraction task
        _update_extraction_progress(db, task_id)
        
        # Log success
        log_repo.create({
            "task_id": task_id,
            "url": url,
            "action": "extract_website",
            "status": "success",
            "response_time": 0
        })
        
        return {
            "status": "success",
            "url": url,
            "emails_found": len(emails),
            "whatsapp_found": len(whatsapp_numbers),
            "quality_score": quality_score
        }
        
    except Exception as e:
        logger.error(f"Error extracting from website {url}: {e}", exc_info=True)
        
        # Use error handler
        error_handler = TaskErrorHandler(db)
        error_handler.log_error(
            task_id=task_id,
            url=url,
            action="extract_website",
            error=e,
            retry_count=self.request.retries,
            max_retries=self.max_retries
        )
        
        # Check if should retry
        if error_handler.should_retry(e, self.request.retries, self.max_retries):
            retry_delay = RetryStrategy.calculate_delay(e, self.request.retries)
            logger.info(f"Retrying task in {retry_delay} seconds")
            raise self.retry(exc=e, countdown=retry_delay)
        else:
            # Send failure notification
            error_handler.notify_task_failure(
                task_id=task_id,
                task_name=self.name,
                error=e,
                retry_count=self.request.retries
            )
            raise
        
    finally:
        if engine:
            engine.close()
        db.close()


@celery_app.task(
    bind=True,
    base=PriorityTask,
    name="scraping_tasks.export_data_task",
    max_retries=2,
    default_retry_delay=10,
    priority=TaskPriority.CRITICAL
)
def export_data_task(
    self,
    filename: str,
    country: Optional[str] = None,
    keyword: Optional[str] = None,
    city: Optional[str] = None,
    institution_type: Optional[str] = None,
    source_platform: Optional[str] = None,
    min_quality_score: Optional[float] = None,
    has_email: Optional[bool] = None,
    has_whatsapp: Optional[bool] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    max_records: Optional[int] = None
) -> Dict[str, Any]:
    """
    Celery task to export contact data to Excel file.
    
    Args:
        filename: Output filename
        country: Filter by country code
        keyword: Filter by search keyword
        city: Filter by city
        institution_type: Filter by institution type
        source_platform: Filter by source platform
        min_quality_score: Minimum quality score filter
        has_email: Filter by email presence
        has_whatsapp: Filter by WhatsApp presence
        date_from: Filter by extraction date (from) - ISO format string
        date_to: Filter by extraction date (to) - ISO format string
        max_records: Maximum number of records to export
        
    Returns:
        Dictionary with export results
    """
    logger.info(f"Starting export task: {filename}")
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Update task state to STARTED
        self.update_state(
            state='STARTED',
            meta={'progress': 0, 'status': 'Initializing export...'}
        )
        
        # Initialize export service
        export_service = ExportService(db)
        
        # Convert date strings to datetime objects
        date_from_dt = datetime.fromisoformat(date_from) if date_from else None
        date_to_dt = datetime.fromisoformat(date_to) if date_to else None
        
        # Update progress
        self.update_state(
            state='STARTED',
            meta={'progress': 20, 'status': 'Querying database...'}
        )
        
        # Export contacts to Excel
        filepath = export_service.export_contacts_to_excel(
            filename=filename,
            country=country,
            keyword=keyword,
            city=city,
            institution_type=institution_type,
            source_platform=source_platform,
            min_quality_score=min_quality_score,
            has_email=has_email,
            has_whatsapp=has_whatsapp,
            date_from=date_from_dt,
            date_to=date_to_dt,
            max_records=max_records
        )
        
        # Update progress
        self.update_state(
            state='STARTED',
            meta={'progress': 80, 'status': 'Formatting Excel file...'}
        )
        
        # Get file size
        from pathlib import Path
        file_size = Path(filepath).stat().st_size
        
        # Count records exported
        import openpyxl
        wb = openpyxl.load_workbook(filepath, read_only=True)
        ws = wb.active
        records_count = ws.max_row - 2  # Subtract header rows
        wb.close()
        
        logger.info(f"Export completed: {filepath} ({records_count} records, {file_size} bytes)")
        
        # Send completion notification (placeholder)
        logger.info(f"Export task completed successfully: {filename}")
        
        return {
            "status": "success",
            "filename": filename,
            "filepath": filepath,
            "records_count": records_count,
            "file_size": file_size,
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except ValueError as e:
        # No data found
        logger.warning(f"Export failed - no data: {e}")
        return {
            "status": "error",
            "message": str(e),
            "filename": filename
        }
        
    except Exception as e:
        logger.error(f"Error in export task: {e}", exc_info=True)
        
        # Check if should retry
        if self.request.retries < self.max_retries:
            retry_delay = 10 * (2 ** self.request.retries)  # Exponential backoff
            logger.info(f"Retrying export task in {retry_delay} seconds")
            raise self.retry(exc=e, countdown=retry_delay)
        else:
            # Send failure notification
            logger.error(f"Export task failed after {self.request.retries} retries: {filename}")
            raise
    finally:
        db.close()
