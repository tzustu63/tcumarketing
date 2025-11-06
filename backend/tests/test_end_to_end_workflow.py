"""
End-to-End Integration Tests for Complete Workflow
Tests the integration of: Scraper → Extractor → Validator → Database
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.database import Base
from app.models.task import Task
from app.models.contact import Contact
from app.models.scraping_log import ScrapingLog
from app.repositories.task_repository import TaskRepository
from app.repositories.contact_repository import ContactRepository
from app.repositories.scraping_log_repository import ScrapingLogRepository
from app.scraper.scraping_engine import ScrapingEngine, PageContent
from app.extractor.contact_extractor import ContactExtractor
from app.extractor.contact_validator import ContactValidator
from app.extractor.html_parser import HTMLParser


# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def db_session():
    """Create a test database session"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_html_with_contacts():
    """Sample HTML with contact information"""
    return """
    <html>
        <head><title>SMA Internasional Jakarta</title></head>
        <body>
            <h1>Kontak Kami</h1>
            <div class="contact-info">
                <p>Email: info@smajakarta.sch.id</p>
                <p>WhatsApp: +62 812-3456-7890</p>
                <p>Alamat: Jakarta Selatan</p>
            </div>
            <div class="about">
                <p>Kami adalah sekolah menengah atas internasional</p>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def sample_social_media_text():
    """Sample social media bio text"""
    return """
    Pusat Bahasa Mandarin Jakarta
    Kursus bahasa Mandarin untuk semua tingkat
    📧 Email: info@mandarincenter.co.id
    📱 WA: 0812-9876-5432
    """


class TestEndToEndWorkflow:
    """Test complete workflow integration"""
    
    def test_complete_website_extraction_workflow(self, db_session, sample_html_with_contacts):
        """
        Test complete workflow: HTML → Extract → Validate → Save
        """
        # Setup repositories
        task_repo = TaskRepository(db_session)
        contact_repo = ContactRepository(db_session)
        log_repo = ScrapingLogRepository(db_session)
        
        # Create a test task
        task = Task(
            keyword="SMA Internasional",
            city="Jakarta",
            target_platforms=["website"],
            max_results=10,
            status="running"
        )
        created_task = task_repo.create(task)
        
        # Initialize components
        html_parser = HTMLParser()
        contact_validator = ContactValidator()
        
        # Step 1: Parse HTML and extract contact info
        url = "https://smajakarta.sch.id"
        parsed_data = html_parser.parse_html(
            sample_html_with_contacts,
            institution_name="SMA Internasional Jakarta"
        )
        
        # Verify extraction
        assert len(parsed_data["emails"]) > 0
        assert len(parsed_data["whatsapp_numbers"]) > 0
        assert parsed_data["institution_type"] == "高中"
        
        # Step 2: Validate contact information
        emails = []
        for email in parsed_data["emails"]:
            result = contact_validator.validate_email(email)
            if result.is_valid:
                emails.append(email)
        
        whatsapp_numbers = []
        for number in parsed_data["whatsapp_numbers"]:
            result = contact_validator.validate_phone(number)
            if result.is_valid:
                whatsapp_numbers.append(result.normalized_value)
        
        assert len(emails) > 0
        assert len(whatsapp_numbers) > 0
        
        # Step 3: Calculate quality score
        quality_score = contact_validator.calculate_quality_score(
            has_email=len(emails) > 0,
            has_whatsapp=len(whatsapp_numbers) > 0,
            source_platform="website",
            has_institution_name=True
        )
        
        assert quality_score >= 90.0  # Should have high quality
        
        # Step 4: Save to database
        contact = Contact(
            task_id=created_task.id,
            institution_name="SMA Internasional Jakarta",
            institution_type=parsed_data["institution_type"],
            source_url=url,
            source_platform="website",
            email=emails[0],
            whatsapp=whatsapp_numbers[0],
            quality_score=quality_score
        )
        
        # Check for duplicates
        is_duplicate = contact_repo.check_duplicate(contact)
        assert not is_duplicate
        
        # Save contact
        saved_contact = contact_repo.create(contact)
        assert saved_contact.id is not None
        
        # Step 5: Log the operation
        log = ScrapingLog(
            task_id=created_task.id,
            url=url,
            action="extract_website",
            status="success"
        )
        saved_log = log_repo.create(log)
        assert saved_log.id is not None
        
        # Step 6: Update task results count
        task_repo.increment_results_count(str(created_task.id))
        updated_task = task_repo.get(str(created_task.id))
        assert updated_task.results_count == 1
        
        # Verify complete workflow
        all_contacts = contact_repo.get_by_task(str(created_task.id))
        assert len(all_contacts) == 1
        assert all_contacts[0].email == emails[0]
        assert all_contacts[0].institution_type == "高中"
    
    def test_social_media_extraction_workflow(self, db_session, sample_social_media_text):
        """
        Test social media extraction workflow
        """
        # Setup repositories
        task_repo = TaskRepository(db_session)
        contact_repo = ContactRepository(db_session)
        
        # Create a test task
        task = Task(
            keyword="Pusat Bahasa Mandarin",
            city="Jakarta",
            target_platforms=["facebook"],
            max_results=10,
            status="running"
        )
        created_task = task_repo.create(task)
        
        # Initialize components
        contact_extractor = ContactExtractor()
        contact_validator = ContactValidator()
        
        # Step 1: Extract from social media text
        contact_info = contact_extractor.extract_from_text(
            sample_social_media_text,
            institution_name="Pusat Bahasa Mandarin Jakarta"
        )
        
        # Verify extraction
        assert len(contact_info.emails) > 0
        assert len(contact_info.whatsapp_numbers) > 0
        assert contact_info.institution_type == "華語中心"
        
        # Step 2: Validate
        valid_emails = [e for e in contact_info.emails 
                       if contact_validator.validate_email(e).is_valid]
        valid_whatsapp = [w for w in contact_info.whatsapp_numbers 
                         if contact_validator.validate_phone(w).is_valid]
        
        assert len(valid_emails) > 0
        assert len(valid_whatsapp) > 0
        
        # Step 3: Calculate quality score (social media source)
        quality_score = contact_validator.calculate_quality_score(
            has_email=True,
            has_whatsapp=True,
            source_platform="facebook",
            has_institution_name=True
        )
        
        assert quality_score >= 85.0  # Good quality but not as high as website
        
        # Step 4: Save to database
        contact = Contact(
            task_id=created_task.id,
            institution_name="Pusat Bahasa Mandarin Jakarta",
            institution_type=contact_info.institution_type,
            source_url="https://facebook.com/mandarincenter",
            source_platform="facebook",
            email=valid_emails[0],
            whatsapp=valid_whatsapp[0],
            quality_score=quality_score
        )
        
        saved_contact = contact_repo.create(contact)
        assert saved_contact.id is not None
        assert saved_contact.institution_type == "華語中心"
    
    def test_duplicate_detection_workflow(self, db_session, sample_html_with_contacts):
        """
        Test that duplicate contacts are properly detected
        """
        task_repo = TaskRepository(db_session)
        contact_repo = ContactRepository(db_session)
        html_parser = HTMLParser()
        
        # Create task
        task = Task(
            keyword="SMA",
            city="Jakarta",
            target_platforms=["website"],
            max_results=10,
            status="running"
        )
        created_task = task_repo.create(task)
        
        # Parse HTML
        parsed_data = html_parser.parse_html(
            sample_html_with_contacts,
            institution_name="SMA Jakarta"
        )
        
        # Create first contact
        contact1 = Contact(
            task_id=created_task.id,
            institution_name="SMA Jakarta",
            institution_type=parsed_data["institution_type"],
            source_url="https://smajakarta.sch.id",
            source_platform="website",
            email=parsed_data["emails"][0] if parsed_data["emails"] else None,
            whatsapp=parsed_data["whatsapp_numbers"][0] if parsed_data["whatsapp_numbers"] else None,
            quality_score=90.0
        )
        
        # Save first contact
        contact_repo.create(contact1)
        
        # Try to save duplicate
        is_duplicate = contact_repo.check_duplicate(contact1)
        assert is_duplicate
        
        # Try with different URL but same email
        contact2 = Contact(
            task_id=created_task.id,
            institution_name="SMA Jakarta Branch",
            institution_type="高中",
            source_url="https://smajakarta.sch.id/branch",
            source_platform="website",
            email=parsed_data["emails"][0] if parsed_data["emails"] else None,
            whatsapp=None,
            quality_score=80.0
        )
        
        # Should not be duplicate (different URL)
        is_duplicate = contact_repo.check_duplicate(contact2)
        assert not is_duplicate
    
    def test_error_handling_workflow(self, db_session):
        """
        Test error handling in the workflow
        """
        task_repo = TaskRepository(db_session)
        log_repo = ScrapingLogRepository(db_session)
        
        # Create task
        task = Task(
            keyword="Test",
            city="Jakarta",
            target_platforms=["website"],
            max_results=10,
            status="running"
        )
        created_task = task_repo.create(task)
        
        # Simulate failed scraping
        error_log = ScrapingLog(
            task_id=created_task.id,
            url="https://invalid-url.com",
            action="extract_website",
            status="failed",
            error_message="Connection timeout"
        )
        
        saved_log = log_repo.create(error_log)
        assert saved_log.status == "failed"
        assert saved_log.error_message is not None
        
        # Verify task can be updated with error
        task.status = "failed"
        task.error_message = "Multiple extraction failures"
        task_repo.update(str(created_task.id), task)
        
        updated_task = task_repo.get(str(created_task.id))
        assert updated_task.status == "failed"
        assert updated_task.error_message is not None
    
    def test_quality_score_calculation_workflow(self, db_session):
        """
        Test quality score calculation for different scenarios
        """
        contact_validator = ContactValidator()
        
        # Scenario 1: Complete info from website
        score1 = contact_validator.calculate_quality_score(
            has_email=True,
            has_whatsapp=True,
            source_platform="website",
            has_institution_name=True
        )
        assert score1 == 100.0
        
        # Scenario 2: Only email from website
        score2 = contact_validator.calculate_quality_score(
            has_email=True,
            has_whatsapp=False,
            source_platform="website",
            has_institution_name=True
        )
        assert score2 == 60.0
        
        # Scenario 3: Complete info from social media
        score3 = contact_validator.calculate_quality_score(
            has_email=True,
            has_whatsapp=True,
            source_platform="facebook",
            has_institution_name=True
        )
        assert score3 == 95.0
        
        # Scenario 4: Only WhatsApp, no institution name
        score4 = contact_validator.calculate_quality_score(
            has_email=False,
            has_whatsapp=True,
            source_platform="instagram",
            has_institution_name=False
        )
        assert score4 == 45.0
    
    def test_institution_classification_workflow(self, db_session):
        """
        Test institution type classification in workflow
        """
        contact_extractor = ContactExtractor()
        
        # Test high school classification
        result1 = contact_extractor.extract_from_text(
            "Hubungi kami di info@sma.sch.id",
            institution_name="SMA Internasional Jakarta"
        )
        assert result1.institution_type == "高中"
        
        # Test language center classification
        result2 = contact_extractor.extract_from_text(
            "Email: contact@mandarin.co.id",
            institution_name="Pusat Bahasa Mandarin"
        )
        assert result2.institution_type == "華語中心"
        
        # Test education agency classification
        result3 = contact_extractor.extract_from_text(
            "Kontak: info@eduagent.com",
            institution_name="Agen Pendidikan Luar Negeri"
        )
        assert result3.institution_type == "代辦"
    
    @patch('app.scraper.scraping_engine.webdriver.Chrome')
    def test_mocked_scraping_workflow(self, mock_chrome, db_session, sample_html_with_contacts):
        """
        Test workflow with mocked scraping engine
        """
        # Setup mock
        mock_driver = MagicMock()
        mock_driver.page_source = sample_html_with_contacts
        mock_driver.title = "SMA Internasional Jakarta"
        mock_driver.current_url = "https://smajakarta.sch.id"
        mock_chrome.return_value = mock_driver
        
        # Setup repositories
        task_repo = TaskRepository(db_session)
        contact_repo = ContactRepository(db_session)
        
        # Create task
        task = Task(
            keyword="SMA Internasional",
            city="Jakarta",
            target_platforms=["website"],
            max_results=10,
            status="running"
        )
        created_task = task_repo.create(task)
        
        # Initialize components
        html_parser = HTMLParser()
        contact_validator = ContactValidator()
        
        # Simulate scraping and extraction
        parsed_data = html_parser.parse_html(
            sample_html_with_contacts,
            institution_name="SMA Internasional Jakarta"
        )
        
        # Validate and save
        if parsed_data["emails"] or parsed_data["whatsapp_numbers"]:
            contact = Contact(
                task_id=created_task.id,
                institution_name="SMA Internasional Jakarta",
                institution_type=parsed_data["institution_type"],
                source_url="https://smajakarta.sch.id",
                source_platform="website",
                email=parsed_data["emails"][0] if parsed_data["emails"] else None,
                whatsapp=parsed_data["whatsapp_numbers"][0] if parsed_data["whatsapp_numbers"] else None,
                quality_score=90.0
            )
            
            contact_repo.create(contact)
            task_repo.increment_results_count(str(created_task.id))
        
        # Verify results
        updated_task = task_repo.get(str(created_task.id))
        assert updated_task.results_count == 1
        
        contacts = contact_repo.get_by_task(str(created_task.id))
        assert len(contacts) == 1
        assert contacts[0].institution_type == "高中"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
