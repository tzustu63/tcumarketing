"""
Test script for multi-country functionality
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.scraper.scraping_engine import ScrapingEngine
from app.scraper.google_scraper import GoogleScraper

def test_google_domains():
    """Test that Google domains are correctly mapped for all countries"""
    print("Testing Google domain mapping...")
    
    engine = ScrapingEngine(headless=True)
    
    test_countries = [
        ('ID', 'google.co.id'),
        ('MY', 'google.com.my'),
        ('SG', 'google.com.sg'),
        ('TH', 'google.co.th'),
        ('VN', 'google.com.vn'),
        ('PH', 'google.com.ph'),
        ('MM', 'google.com.mm'),
        ('KH', 'google.com.kh'),
        ('IN', 'google.co.in'),
        ('HK', 'google.com.hk'),
        ('MO', 'google.com'),
    ]
    
    all_passed = True
    for country_code, expected_domain in test_countries:
        actual_domain = engine.get_google_domain(country_code)
        if actual_domain == expected_domain:
            print(f"✅ {country_code}: {actual_domain}")
        else:
            print(f"❌ {country_code}: Expected {expected_domain}, got {actual_domain}")
            all_passed = False
    
    engine.close()
    
    if all_passed:
        print("\n✅ All Google domain mappings are correct!")
    else:
        print("\n❌ Some Google domain mappings are incorrect!")
    
    return all_passed


def test_google_scraper_initialization():
    """Test that GoogleScraper initializes correctly with different countries"""
    print("\nTesting GoogleScraper initialization...")
    
    test_countries = ['ID', 'MY', 'SG', 'TH', 'VN']
    
    all_passed = True
    for country_code in test_countries:
        try:
            engine = ScrapingEngine(headless=True)
            scraper = GoogleScraper(engine, country_code=country_code)
            expected_domain = GoogleScraper.GOOGLE_DOMAINS.get(country_code, 'google.com')
            
            if expected_domain in scraper.base_url:
                print(f"✅ {country_code}: GoogleScraper initialized with {scraper.base_url}")
            else:
                print(f"❌ {country_code}: Expected {expected_domain} in URL, got {scraper.base_url}")
                all_passed = False
            
            engine.close()
        except Exception as e:
            print(f"❌ {country_code}: Failed to initialize - {e}")
            all_passed = False
    
    if all_passed:
        print("\n✅ All GoogleScraper initializations successful!")
    else:
        print("\n❌ Some GoogleScraper initializations failed!")
    
    return all_passed


def test_model_fields():
    """Test that models have country fields"""
    print("\nTesting model fields...")
    
    from app.models.task import Task
    from app.models.contact import Contact
    
    # Check Task model
    task_columns = [col.name for col in Task.__table__.columns]
    if 'country' in task_columns:
        print("✅ Task model has 'country' field")
    else:
        print("❌ Task model missing 'country' field")
        return False
    
    # Check Contact model
    contact_columns = [col.name for col in Contact.__table__.columns]
    if 'country' in contact_columns:
        print("✅ Contact model has 'country' field")
    else:
        print("❌ Contact model missing 'country' field")
        return False
    
    print("\n✅ All model fields are correct!")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Multi-Country Functionality Test")
    print("=" * 60)
    
    results = []
    
    # Test 1: Google domain mapping
    results.append(("Google Domain Mapping", test_google_domains()))
    
    # Test 2: GoogleScraper initialization
    results.append(("GoogleScraper Initialization", test_google_scraper_initialization()))
    
    # Test 3: Model fields
    results.append(("Model Fields", test_model_fields()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed!")
        sys.exit(1)
