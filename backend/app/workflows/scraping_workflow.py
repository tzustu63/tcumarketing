"""
Complete Scraping Workflow Orchestrator
Integrates: Scraper → Extractor → Validator → Database
"""
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from sqlalchemy.orm import Session

from app.scraper.scraping_engine import ScrapingEngine
from app.scraper.google_scraper import GoogleScraper, SearchResult
from app.scraper.contact_page_finder import ContactPageFinder
from app.scraper.facebook_scraper import FacebookScraper
from app.scraper.instagram_scraper import InstagramScraper
from app.scraper.social_media_extractor import SocialMediaExtractor
from app.extractor.contact_extractor import ContactExtractor
from app.extractor.contact_validator import ContactValidator
from app.extractor.html_parser import HTMLParser
from app.models.contact import Contact
from app.models.scraping_log import ScrapingLog
from app.repositories.contact_repository import ContactRepository
from app.repositories.scraping_log_repository import ScrapingLogRepository
from app.repositories.task_repository import TaskRepository

logger = logging.getLogger(__name__)


@dataclass
class WorkflowResult:
    """Result of workflow execution"""
    success: bool
    contacts_found: int
    contacts_saved: int
    duplicates_skipped: int
    errors: List[str]
    execution_time: float
    details: Dict[str, Any]


class ScrapingWorkflow:
    """
    Orchestrates the complete scraping workflow:
    1. Search Google for results
    2. Extract contact information from websites/social media
    3. Validate extracted data
    4. Save to database
    5. Log all operations
    """
    
    def __init__(
        self,
        db: Session,
        use_anti_detection: bool = True,
        use_rate_limiting: bool = True
    ):
        """
        Initialize workflow orchestrator
        
        Args:
            db: Database session
            use_anti_detection: Enable anti-detection measures
            use_rate_limiting: Enable rate limiting
        """
        self.db = db
        self.use_anti_detection = use_anti_detection
        self.use_rate_limiting = use_rate_limiting
        
        # Initialize repositories
        self.task_repo = TaskRepository(db)
        self.contact_repo = ContactRepository(db)
        self.log_repo = ScrapingLogRepository(db)
        
        # Initialize extractors and validators
        self.contact_extractor = ContactExtractor()
        self.contact_validator = ContactValidator()
        self.html_parser = HTMLParser()
        self.social_extractor = SocialMediaExtractor()
        
        logger.info("ScrapingWorkflow initialized")
    
    def execute_google_search_workflow(
        self,
        task_id: str,
        keyword: str,
        city: str,
        target_platforms: List[str],
        max_results: int = 100
    ) -> WorkflowResult:
        """
        Execute complete Google search workflow
        
        Args:
            task_id: Task ID for tracking
            keyword: Search keyword
            city: City to search in
            target_platforms: Target platforms (website, facebook, instagram)
            max_results: Maximum number of results to process
            
        Returns:
            WorkflowResult with execution details
        """
        start_time = datetime.utcnow()
        errors = []
        contacts_found = 0
        contacts_saved = 0
        duplicates_skipped = 0
        
        engine = None
        
        try:
            # Step 1: Initialize scraping engine
            logger.info(f"Starting Google search workflow for task {task_id}")
            engine = ScrapingEngine(
                headless=True,
                use_anti_detection=self.use_anti_detection,
                use_rate_limiting=self.use_rate_limiting
            )
            
            # Step 2: Search Google
            google_scraper = GoogleScraper(engine)
            query = f"{keyword} {city}"
            max_pages = min(5, (max_results // 10) + 1)
            
            logger.info(f"Searching Google: {query}")
            search_results = google_scraper.search_google(query, max_pages=max_pages)
            
            # Log search operation
            self.log_repo.create(ScrapingLog(
                task_id=task_id,
                url=f"google_search:{query}",
                action="google_search",
                status="success"
            ))
            
            # Step 3: Filter by target platforms
            filtered_results = [
                r for r in search_results
                if r.platform in target_platforms or "website" in target_platforms
            ]
            
            logger.info(f"Found {len(filtered_results)} results matching target platforms")
            
            # Step 4: Process each result
            for i, result in enumerate(filtered_results[:max_results]):
                try:
                    if result.platform == "facebook":
                        workflow_result = self.execute_facebook_extraction_workflow(
                            task_id, result.url, result.title
                        )
                    elif result.platform == "instagram":
                        workflow_result = self.execute_instagram_extraction_workflow(
                            task_id, result.url, result.title
                        )
                    else:
                        workflow_result = self.execute_website_extraction_workflow(
                            task_id, result.url, result.title
                        )
                    
                    contacts_found += workflow_result.contacts_found
                    contacts_saved += workflow_result.contacts_saved
                    duplicates_skipped += workflow_result.duplicates_skipped
                    errors.extend(workflow_result.errors)
                    
                    # Update task progress
                    progress = int((i + 1) / len(filtered_results[:max_results]) * 100)
                    task = self.task_repo.get(task_id)
                    if task:
                        task.progress = progress
                        self.db.commit()
                    
                except Exception as e:
                    logger.error(f"Error processing result {result.url}: {e}")
                    errors.append(f"Error processing {result.url}: {str(e)}")
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return WorkflowResult(
                success=True,
                contacts_found=contacts_found,
                contacts_saved=contacts_saved,
                duplicates_skipped=duplicates_skipped,
                errors=errors,
                execution_time=execution_time,
                details={
                    "search_query": query,
                    "results_found": len(search_results),
                    "results_processed": len(filtered_results[:max_results])
                }
            )
            
        except Exception as e:
            logger.error(f"Error in Google search workflow: {e}", exc_info=True)
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Log error
            self.log_repo.create(ScrapingLog(
                task_id=task_id,
                url=f"google_search:{keyword}",
                action="google_search",
                status="failed",
                error_message=str(e)
            ))
            
            return WorkflowResult(
                success=False,
                contacts_found=contacts_found,
                contacts_saved=contacts_saved,
                duplicates_skipped=duplicates_skipped,
                errors=[str(e)] + errors,
                execution_time=execution_time,
                details={"error": str(e)}
            )
            
        finally:
            if engine:
                engine.close()
    
    def execute_website_extraction_workflow(
        self,
        task_id: str,
        url: str,
        institution_name: str = ""
    ) -> WorkflowResult:
        """
        Execute website extraction workflow
        
        Args:
            task_id: Task ID for tracking
            url: Website URL
            institution_name: Institution name
            
        Returns:
            WorkflowResult with execution details
        """
        start_time = datetime.utcnow()
        errors = []
        
        engine = None
        
        try:
            # Step 1: Initialize scraping engine
            engine = ScrapingEngine(
                headless=True,
                use_anti_detection=self.use_anti_detection,
                use_rate_limiting=self.use_rate_limiting
            )
            
            # Step 2: Find contact page
            contact_finder = ContactPageFinder(engine)
            contact_url = contact_finder.find_contact_page(url)
            if not contact_url:
                contact_url = url
                logger.info(f"No contact page found, using main URL: {url}")
            
            # Step 3: Fetch page content
            page_content = engine.fetch_page_with_retry(contact_url)
            
            # Step 4: Parse HTML and extract contact info
            parsed_data = self.html_parser.parse_html(
                page_content.html,
                institution_name=institution_name
            )
            
            # Step 5: Validate contact information
            valid_emails = []
            for email in parsed_data.get("emails", []):
                result = self.contact_validator.validate_email(email)
                if result.is_valid:
                    valid_emails.append(email)
            
            valid_whatsapp = []
            for number in parsed_data.get("whatsapp_numbers", []):
                result = self.contact_validator.validate_phone(number)
                if result.is_valid:
                    valid_whatsapp.append(result.normalized_value)
            
            # Step 6: Calculate quality score
            quality_score = self.contact_validator.calculate_quality_score(
                has_email=len(valid_emails) > 0,
                has_whatsapp=len(valid_whatsapp) > 0,
                source_platform="website",
                has_institution_name=bool(institution_name)
            )
            
            # Step 7: Save to database if contact info found
            contacts_saved = 0
            duplicates_skipped = 0
            
            if valid_emails or valid_whatsapp:
                contact = Contact(
                    task_id=task_id,
                    institution_name=institution_name or parsed_data.get("title", "Unknown"),
                    institution_type=parsed_data.get("institution_type"),
                    source_url=url,
                    source_platform="website",
                    email=valid_emails[0] if valid_emails else None,
                    whatsapp=valid_whatsapp[0] if valid_whatsapp else None,
                    additional_info={
                        "all_emails": valid_emails,
                        "all_whatsapp": valid_whatsapp,
                        "contact_page_url": contact_url
                    },
                    quality_score=quality_score
                )
                
                # Check for duplicates
                if not self.contact_repo.check_duplicate(contact):
                    self.contact_repo.create(contact)
                    self.task_repo.increment_results_count(task_id)
                    contacts_saved = 1
                    logger.info(f"Saved contact for: {institution_name}")
                else:
                    duplicates_skipped = 1
                    logger.info(f"Duplicate contact skipped: {url}")
            
            # Step 8: Log success
            self.log_repo.create(ScrapingLog(
                task_id=task_id,
                url=url,
                action="extract_website",
                status="success"
            ))
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return WorkflowResult(
                success=True,
                contacts_found=1 if (valid_emails or valid_whatsapp) else 0,
                contacts_saved=contacts_saved,
                duplicates_skipped=duplicates_skipped,
                errors=errors,
                execution_time=execution_time,
                details={
                    "url": url,
                    "emails_found": len(valid_emails),
                    "whatsapp_found": len(valid_whatsapp),
                    "quality_score": quality_score
                }
            )
            
        except Exception as e:
            logger.error(f"Error in website extraction workflow: {e}", exc_info=True)
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Log error
            self.log_repo.create(ScrapingLog(
                task_id=task_id,
                url=url,
                action="extract_website",
                status="failed",
                error_message=str(e)
            ))
            
            return WorkflowResult(
                success=False,
                contacts_found=0,
                contacts_saved=0,
                duplicates_skipped=0,
                errors=[str(e)],
                execution_time=execution_time,
                details={"error": str(e)}
            )
            
        finally:
            if engine:
                engine.close()
    
    def execute_facebook_extraction_workflow(
        self,
        task_id: str,
        url: str,
        page_name: str = ""
    ) -> WorkflowResult:
        """
        Execute Facebook extraction workflow
        
        Args:
            task_id: Task ID for tracking
            url: Facebook page URL
            page_name: Page name
            
        Returns:
            WorkflowResult with execution details
        """
        return self._execute_social_media_workflow(
            task_id, url, "facebook", page_name
        )
    
    def execute_instagram_extraction_workflow(
        self,
        task_id: str,
        url: str,
        page_name: str = ""
    ) -> WorkflowResult:
        """
        Execute Instagram extraction workflow
        
        Args:
            task_id: Task ID for tracking
            url: Instagram profile URL
            page_name: Profile name
            
        Returns:
            WorkflowResult with execution details
        """
        return self._execute_social_media_workflow(
            task_id, url, "instagram", page_name
        )
    
    def _execute_social_media_workflow(
        self,
        task_id: str,
        url: str,
        platform: str,
        page_name: str = ""
    ) -> WorkflowResult:
        """
        Execute social media extraction workflow (Facebook/Instagram)
        
        Args:
            task_id: Task ID for tracking
            url: Social media URL
            platform: Platform name (facebook/instagram)
            page_name: Page/profile name
            
        Returns:
            WorkflowResult with execution details
        """
        start_time = datetime.utcnow()
        errors = []
        
        engine = None
        
        try:
            # Step 1: Initialize scraping engine
            engine = ScrapingEngine(
                headless=True,
                use_anti_detection=self.use_anti_detection,
                use_rate_limiting=self.use_rate_limiting
            )
            
            # Step 2: Extract based on platform
            if platform == "facebook":
                fb_scraper = FacebookScraper(engine)
                profile_data = fb_scraper.extract_contact_info(url)
                text = profile_data.get("about", "") + " " + profile_data.get("description", "")
                external_links = profile_data.get("external_links", [])
            elif platform == "instagram":
                ig_scraper = InstagramScraper(engine)
                profile_data = ig_scraper.extract_contact_info(url)
                text = profile_data.get("bio", "") + " " + profile_data.get("description", "")
                external_links = profile_data.get("external_links", [])
            else:
                raise ValueError(f"Unsupported platform: {platform}")
            
            # Step 3: Extract contact information
            contact_info = self.social_extractor.extract_from_social_media(
                text=text,
                platform=platform,
                external_links=external_links
            )
            
            # Step 4: Validate contact information
            valid_emails = []
            for email in contact_info.emails:
                result = self.contact_validator.validate_email(email)
                if result.is_valid:
                    valid_emails.append(email)
            
            valid_whatsapp = []
            for number in contact_info.whatsapp_numbers:
                result = self.contact_validator.validate_phone(number)
                if result.is_valid:
                    valid_whatsapp.append(result.normalized_value)
            
            # Step 5: Determine institution type
            institution_type = self.social_extractor.extract_institution_type_from_social(
                text, page_name
            )
            
            # Step 6: Calculate quality score
            quality_score = self.contact_validator.calculate_quality_score(
                has_email=len(valid_emails) > 0,
                has_whatsapp=len(valid_whatsapp) > 0,
                source_platform=platform,
                has_institution_name=bool(page_name)
            )
            
            # Step 7: Save to database if contact info found
            contacts_saved = 0
            duplicates_skipped = 0
            
            if valid_emails or valid_whatsapp:
                contact = Contact(
                    task_id=task_id,
                    institution_name=page_name or profile_data.get("name", "Unknown"),
                    institution_type=institution_type,
                    source_url=url,
                    source_platform=platform,
                    email=valid_emails[0] if valid_emails else None,
                    whatsapp=valid_whatsapp[0] if valid_whatsapp else None,
                    additional_info={
                        "all_emails": valid_emails,
                        "all_whatsapp": valid_whatsapp,
                        "markers_found": contact_info.markers_found,
                        "external_links": contact_info.external_links
                    },
                    quality_score=quality_score
                )
                
                # Check for duplicates
                if not self.contact_repo.check_duplicate(contact):
                    self.contact_repo.create(contact)
                    self.task_repo.increment_results_count(task_id)
                    contacts_saved = 1
                    logger.info(f"Saved contact for: {page_name}")
                else:
                    duplicates_skipped = 1
                    logger.info(f"Duplicate contact skipped: {url}")
            
            # Step 8: Log success
            self.log_repo.create(ScrapingLog(
                task_id=task_id,
                url=url,
                action=f"extract_{platform}",
                status="success"
            ))
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return WorkflowResult(
                success=True,
                contacts_found=1 if (valid_emails or valid_whatsapp) else 0,
                contacts_saved=contacts_saved,
                duplicates_skipped=duplicates_skipped,
                errors=errors,
                execution_time=execution_time,
                details={
                    "url": url,
                    "platform": platform,
                    "emails_found": len(valid_emails),
                    "whatsapp_found": len(valid_whatsapp),
                    "quality_score": quality_score
                }
            )
            
        except Exception as e:
            logger.error(f"Error in {platform} extraction workflow: {e}", exc_info=True)
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Log error
            self.log_repo.create(ScrapingLog(
                task_id=task_id,
                url=url,
                action=f"extract_{platform}",
                status="failed",
                error_message=str(e)
            ))
            
            return WorkflowResult(
                success=False,
                contacts_found=0,
                contacts_saved=0,
                duplicates_skipped=0,
                errors=[str(e)],
                execution_time=execution_time,
                details={"error": str(e)}
            )
            
        finally:
            if engine:
                engine.close()
