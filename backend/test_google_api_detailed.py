"""
Detailed test script for Google Custom Search API
"""
import sys
import os
import requests

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings

def test_google_api_detailed():
    """Test Google Custom Search API with detailed error info"""
    print("=" * 60)
    print("Detailed Google Custom Search API Test")
    print("=" * 60)
    
    api_key = settings.GOOGLE_API_KEY
    cse_id = settings.GOOGLE_CSE_ID
    
    print(f"\nAPI Key: {api_key[:20]}..." if api_key else "Not configured")
    print(f"CSE ID: {cse_id}")
    
    if not api_key or not cse_id:
        print("\n❌ ERROR: Credentials not configured!")
        return False
    
    # Test API request
    url = "https://customsearch.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": "test",
        "num": 1
    }
    
    print(f"\n📡 Making test request...")
    print(f"URL: {url}")
    print(f"Query: test")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"Response Headers:")
        for key, value in response.headers.items():
            if key.lower() in ['content-type', 'x-goog-api-key', 'x-goog-api-client']:
                print(f"  {key}: {value}")
        
        print(f"\n📄 Response Body:")
        print(response.text[:500])
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ API is working!")
            print(f"Search Information:")
            if 'searchInformation' in data:
                print(f"  Total Results: {data['searchInformation'].get('totalResults', 0)}")
                print(f"  Search Time: {data['searchInformation'].get('searchTime', 0)}s")
            return True
        else:
            print(f"\n❌ API Error!")
            try:
                error_data = response.json()
                if 'error' in error_data:
                    print(f"Error Code: {error_data['error'].get('code')}")
                    print(f"Error Message: {error_data['error'].get('message')}")
                    if 'errors' in error_data['error']:
                        for err in error_data['error']['errors']:
                            print(f"  - {err.get('reason')}: {err.get('message')}")
            except:
                pass
            return False
            
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_google_api_detailed()
    sys.exit(0 if success else 1)
