"""
Test script to verify Celery setup and configuration
"""
import sys
from app.celery_app import celery_app
from app.tasks import scrape_google_task, extract_website_task, extract_social_task

def test_celery_configuration():
    """Test Celery configuration"""
    print("Testing Celery Configuration...")
    print(f"Broker URL: {celery_app.conf.broker_url}")
    print(f"Result Backend: {celery_app.conf.result_backend}")
    print(f"Task Serializer: {celery_app.conf.task_serializer}")
    print(f"Worker Concurrency: {celery_app.conf.worker_concurrency}")
    print(f"Task Time Limit: {celery_app.conf.task_time_limit}")
    print(f"Task Max Retries: {celery_app.conf.task_max_retries}")
    print("✓ Celery configuration loaded successfully\n")

def test_task_registration():
    """Test that tasks are registered"""
    print("Testing Task Registration...")
    
    registered_tasks = list(celery_app.tasks.keys())
    print(f"Total registered tasks: {len(registered_tasks)}")
    
    expected_tasks = [
        "scraping_tasks.scrape_google_task",
        "scraping_tasks.extract_website_task",
        "scraping_tasks.extract_social_task"
    ]
    
    for task_name in expected_tasks:
        if task_name in registered_tasks:
            print(f"✓ {task_name} registered")
        else:
            print(f"✗ {task_name} NOT registered")
            return False
    
    print("✓ All tasks registered successfully\n")
    return True

def test_task_signatures():
    """Test task signatures"""
    print("Testing Task Signatures...")
    
    # Test scrape_google_task signature
    try:
        sig = scrape_google_task.s("test-task-id")
        print(f"✓ scrape_google_task signature: {sig}")
    except Exception as e:
        print(f"✗ scrape_google_task signature failed: {e}")
        return False
    
    # Test extract_website_task signature
    try:
        sig = extract_website_task.s("test-task-id", "https://example.com", "Test Institution")
        print(f"✓ extract_website_task signature: {sig}")
    except Exception as e:
        print(f"✗ extract_website_task signature failed: {e}")
        return False
    
    # Test extract_social_task signature
    try:
        sig = extract_social_task.s("test-task-id", "https://facebook.com/test", "facebook", "Test Page")
        print(f"✓ extract_social_task signature: {sig}")
    except Exception as e:
        print(f"✗ extract_social_task signature failed: {e}")
        return False
    
    print("✓ All task signatures created successfully\n")
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("Celery Setup Verification")
    print("=" * 60 + "\n")
    
    try:
        test_celery_configuration()
        
        if not test_task_registration():
            print("\n✗ Task registration test failed")
            sys.exit(1)
        
        if not test_task_signatures():
            print("\n✗ Task signature test failed")
            sys.exit(1)
        
        print("=" * 60)
        print("✓ All tests passed! Celery is configured correctly.")
        print("=" * 60)
        
        print("\nTo start the Celery worker, run:")
        print("  celery -A app.celery_app worker --loglevel=info")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
