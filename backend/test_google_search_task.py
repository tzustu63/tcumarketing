"""
Test Google Search Task with API
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.scraper.google_api_scraper import GoogleAPISearcher

def test_google_search():
    """Test Google Custom Search API with different queries"""
    print("=" * 70)
    print("測試 Google Custom Search API")
    print("=" * 70)
    
    # Check configuration
    print(f"\n配置檢查:")
    print(f"  API Key: {'✅ 已配置' if settings.GOOGLE_API_KEY else '❌ 未配置'}")
    print(f"  CSE ID: {'✅ 已配置' if settings.GOOGLE_CSE_ID else '❌ 未配置'}")
    
    if not settings.GOOGLE_API_KEY or not settings.GOOGLE_CSE_ID:
        print("\n❌ Google API 未配置！")
        return False
    
    # Test queries
    test_cases = [
        {
            "query": "Agen Pendidikan Jakarta",
            "country": "ID",
            "max_results": 5,
            "description": "印尼雅加達教育代辦"
        },
        {
            "query": "獨立中學 Kuala Lumpur",
            "country": "MY",
            "max_results": 5,
            "description": "馬來西亞吉隆坡獨立中學"
        },
        {
            "query": "華語中心 Singapore",
            "country": "SG",
            "max_results": 3,
            "description": "新加坡華語中心"
        }
    ]
    
    searcher = GoogleAPISearcher()
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 70}")
        print(f"測試案例 {i}: {test_case['description']}")
        print(f"{'=' * 70}")
        print(f"查詢: {test_case['query']}")
        print(f"國家: {test_case['country']}")
        print(f"最大結果數: {test_case['max_results']}")
        
        try:
            results = searcher.search(
                query=test_case['query'],
                max_results=test_case['max_results'],
                country_code=test_case['country']
            )
            
            print(f"\n✅ 搜尋成功！找到 {len(results)} 個結果")
            
            if results:
                print(f"\n前 {min(3, len(results))} 個結果:")
                for j, result in enumerate(results[:3], 1):
                    print(f"\n  {j}. {result.title}")
                    print(f"     URL: {result.url}")
                    print(f"     平台: {result.platform}")
                    print(f"     描述: {result.description[:80]}...")
            else:
                print(f"\nℹ️  該查詢沒有找到結果（這是正常的，可能該關鍵字沒有相關網頁）")
            
        except Exception as e:
            print(f"\n❌ 搜尋失敗: {e}")
            all_passed = False
    
    print(f"\n{'=' * 70}")
    print("測試總結")
    print(f"{'=' * 70}")
    
    if all_passed:
        print("✅ 所有測試通過！Google Custom Search API 運作正常。")
        print("\n建議:")
        print("  1. 系統已配置為優先使用 Google API")
        print("  2. 如果 API 失敗，會自動回退到網頁爬蟲")
        print("  3. 每日免費配額: 100 次搜尋")
        return True
    else:
        print("❌ 部分測試失敗，請檢查錯誤訊息。")
        return False

if __name__ == "__main__":
    import time
    print("\n⏳ 開始測試...\n")
    time.sleep(1)
    
    success = test_google_search()
    
    print(f"\n{'=' * 70}\n")
    sys.exit(0 if success else 1)
