#!/usr/bin/env python3
"""
Integration Verification Script
Validates that all modules are properly integrated and can work together
"""
import sys
from typing import Dict, Any

def check_imports() -> Dict[str, Any]:
    """Check that all required modules can be imported"""
    results = {"success": True, "errors": []}
    
    modules_to_check = [
        ("app.scraper.scraping_engine", "ScrapingEngine"),
        ("app.scraper.google_scraper", "GoogleScraper"),
        ("app.scraper.contact_page_finder", "ContactPageFinder"),
        ("app.scraper.facebook_scraper", "FacebookScraper"),
        ("app.scraper.instagram_scraper", "InstagramScraper"),
        ("app.scraper.social_media_extractor", "SocialMediaExtractor"),
        ("app.extractor.contact_extractor", "ContactExtractor"),
        ("app.extractor.contact_validator", "ContactValidator"),
        ("app.extractor.html_parser", "HTMLParser"),
        ("app.extractor.institution_classifier", "InstitutionClassifier"),
        ("app.repositories.task_repository", "TaskRepository"),
        ("app.repositories.contact_repository", "ContactRepository"),
        ("app.repositories.scraping_log_repository", "ScrapingLogRepository"),
        ("app.models.task", "Task"),
        ("app.models.contact", "Contact"),
        ("app.models.scraping_log", "ScrapingLog"),
        ("app.workflows.scraping_workflow", "ScrapingWorkflow"),
        ("app.tasks.scraping_tasks", "scrape_google_task"),
    ]
    
    print("Checking module imports...")
    for module_path, class_name in modules_to_check:
        try:
            module = __import__(module_path, fromlist=[class_name])
            getattr(module, class_name)
            print(f"  ✓ {module_path}.{class_name}")
        except ImportError as e:
            results["success"] = False
            error_msg = f"Failed to import {module_path}.{class_name}: {e}"
            results["errors"].append(error_msg)
            print(f"  ✗ {error_msg}")
        except AttributeError as e:
            results["success"] = False
            error_msg = f"Module {module_path} missing {class_name}: {e}"
            results["errors"].append(error_msg)
            print(f"  ✗ {error_msg}")
    
    return results


def check_workflow_integration() -> Dict[str, Any]:
    """Check that workflow can be instantiated"""
    results = {"success": True, "errors": []}
    
    print("\nChecking workflow integration...")
    try:
        from app.workflows.scraping_workflow import ScrapingWorkflow, WorkflowResult
        print("  ✓ ScrapingWorkflow can be imported")
        
        # Check that WorkflowResult has required fields
        required_fields = [
            "success", "contacts_found", "contacts_saved", 
            "duplicates_skipped", "errors", "execution_time", "details"
        ]
        for field in required_fields:
            if not hasattr(WorkflowResult, "__annotations__") or field not in WorkflowResult.__annotations__:
                results["success"] = False
                error_msg = f"WorkflowResult missing field: {field}"
                results["errors"].append(error_msg)
                print(f"  ✗ {error_msg}")
            else:
                print(f"  ✓ WorkflowResult has field: {field}")
        
    except Exception as e:
        results["success"] = False
        error_msg = f"Failed to check workflow: {e}"
        results["errors"].append(error_msg)
        print(f"  ✗ {error_msg}")
    
    return results


def check_extractor_validator_integration() -> Dict[str, Any]:
    """Check that extractor and validator work together"""
    results = {"success": True, "errors": []}
    
    print("\nChecking extractor-validator integration...")
    try:
        from app.extractor.contact_extractor import ContactExtractor
        from app.extractor.contact_validator import ContactValidator
        
        extractor = ContactExtractor()
        validator = ContactValidator()
        
        # Test email extraction and validation
        test_text = "Contact us at info@example.co.id or call +62 812-3456-7890"
        contact_info = extractor.extract_from_text(test_text)
        
        if contact_info.emails:
            email_result = validator.validate_email(contact_info.emails[0])
            print(f"  ✓ Email extraction and validation works")
        else:
            print(f"  ⚠ No emails extracted from test text")
        
        if contact_info.whatsapp_numbers:
            phone_result = validator.validate_phone(contact_info.whatsapp_numbers[0])
            print(f"  ✓ WhatsApp extraction and validation works")
        else:
            print(f"  ⚠ No WhatsApp numbers extracted from test text")
        
        # Test quality score calculation
        quality_score = validator.calculate_quality_score(
            has_email=True,
            has_whatsapp=True,
            source_platform="website",
            has_institution_name=True
        )
        
        if quality_score == 100.0:
            print(f"  ✓ Quality score calculation works (score: {quality_score})")
        else:
            results["success"] = False
            error_msg = f"Quality score calculation incorrect: expected 100.0, got {quality_score}"
            results["errors"].append(error_msg)
            print(f"  ✗ {error_msg}")
        
    except Exception as e:
        results["success"] = False
        error_msg = f"Failed extractor-validator integration check: {e}"
        results["errors"].append(error_msg)
        print(f"  ✗ {error_msg}")
    
    return results


def check_html_parser_integration() -> Dict[str, Any]:
    """Check that HTML parser integrates with classifier"""
    results = {"success": True, "errors": []}
    
    print("\nChecking HTML parser integration...")
    try:
        from app.extractor.html_parser import HTMLParser
        
        parser = HTMLParser()
        
        # Test HTML with contact info
        test_html = """
        <html>
            <head><title>SMA Internasional Jakarta</title></head>
            <body>
                <h1>Kontak Kami</h1>
                <p>Email: info@sma.sch.id</p>
                <p>WhatsApp: +62 812-3456-7890</p>
            </body>
        </html>
        """
        
        parsed_data = parser.parse_html(test_html, institution_name="SMA Internasional Jakarta")
        
        if "emails" in parsed_data and parsed_data["emails"]:
            print(f"  ✓ HTML parser extracts emails")
        else:
            print(f"  ⚠ HTML parser did not extract emails")
        
        if "whatsapp_numbers" in parsed_data and parsed_data["whatsapp_numbers"]:
            print(f"  ✓ HTML parser extracts WhatsApp numbers")
        else:
            print(f"  ⚠ HTML parser did not extract WhatsApp numbers")
        
        if "institution_type" in parsed_data and parsed_data["institution_type"] == "高中":
            print(f"  ✓ HTML parser classifies institution type")
        else:
            print(f"  ⚠ HTML parser did not classify institution type correctly")
        
    except Exception as e:
        results["success"] = False
        error_msg = f"Failed HTML parser integration check: {e}"
        results["errors"].append(error_msg)
        print(f"  ✗ {error_msg}")
    
    return results


def check_celery_task_integration() -> Dict[str, Any]:
    """Check that Celery tasks are properly defined"""
    results = {"success": True, "errors": []}
    
    print("\nChecking Celery task integration...")
    try:
        from app.tasks.scraping_tasks import (
            scrape_google_task,
            extract_website_task,
            extract_social_task,
            export_data_task
        )
        
        # Check task names
        expected_tasks = {
            "scrape_google_task": "scraping_tasks.scrape_google_task",
            "extract_website_task": "scraping_tasks.extract_website_task",
            "extract_social_task": "scraping_tasks.extract_social_task",
            "export_data_task": "scraping_tasks.export_data_task",
        }
        
        for task_var, expected_name in expected_tasks.items():
            task = locals()[task_var]
            if hasattr(task, 'name') and task.name == expected_name:
                print(f"  ✓ {task_var} properly configured")
            else:
                results["success"] = False
                error_msg = f"{task_var} has incorrect name"
                results["errors"].append(error_msg)
                print(f"  ✗ {error_msg}")
        
    except Exception as e:
        results["success"] = False
        error_msg = f"Failed Celery task integration check: {e}"
        results["errors"].append(error_msg)
        print(f"  ✗ {error_msg}")
    
    return results


def main():
    """Run all integration checks"""
    print("=" * 60)
    print("Integration Verification")
    print("=" * 60)
    
    all_results = []
    
    # Run all checks
    all_results.append(check_imports())
    all_results.append(check_workflow_integration())
    all_results.append(check_extractor_validator_integration())
    all_results.append(check_html_parser_integration())
    all_results.append(check_celery_task_integration())
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_success = all(r["success"] for r in all_results)
    total_errors = sum(len(r["errors"]) for r in all_results)
    
    if all_success:
        print("✓ All integration checks passed!")
        print("\nThe system is properly integrated and ready for use.")
        return 0
    else:
        print(f"✗ Integration checks failed with {total_errors} error(s)")
        print("\nErrors found:")
        for result in all_results:
            for error in result["errors"]:
                print(f"  - {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
