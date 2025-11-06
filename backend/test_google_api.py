"""
Test script for Google Custom Search API
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.scraper.google_api_scraper import GoogleAPISearcher

def test_google_api():
    """Test Google Custom Search API"""
    print("=" * 60)
    print("Testing Google Custom Search API")
    print("=" * 60)
    
    # Check configuration
    print(f"\nAPI Key: {settings.GOOGLE_API_KEY[:20]}..." if settings.GOOGLE_API_KEY else "Not configured")
    print(f"CSE ID: {settings.GOOGLE_CSE_ID}")
    
    if not settings.GOOGLE_API_KEY or not settings.GOOGLE_CSE_ID:
        print("\n❌ ERROR: Google API credentials not configured!")
        print("Please set GOOGLE_API_KEY and GOOGLE_CSE_ID in .env file")
        return False
    
    try:
        # Initialize searcher
        print("\n📡 Initializing Google API Searcher...")
        searcher = GoogleAPISearcher()
        
        # Test search
        query = "Agen Pendidikan Jakarta"
        print(f"\n🔍 Searching for: {query}")
        print(f"Country: ID (Indonesia)")
        print(f"Max results: 5")
        
        results = searcher.search(
            query=query,
            max_results=5,
            country_code="ID",
            language="id"
        )
        
        print(f"\n✅ Search completed!")
        print(f"Found {len(results)} results\n")
        
        # Display results
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.title}")
            print(f"   URL: {result.url}")
            print(f"   Platform: {result.platform}")
            print(f"   Description: {result.description[:100]}...")
            print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_google_api()
    sys.exit(0 if success else 1)
