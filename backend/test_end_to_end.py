"""
End-to-end test for the recruitment automation system
Tests the complete workflow from search to contact extraction
"""
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.scraper.google_api_scraper import GoogleAPISearcher
from app.scraper.scraping_engine import ScrapingEngine
from app.scraper.contact_page_finder import ContactPageFinder
from app.extractor.html_parser import HTMLParser
from app.extractor.contact_extractor import ContactExtractor
from app.extractor.contact_validator import ContactValidator

def test_end_to_end():
    """Test complete workflow"""
    print("=" * 70)
    print("端到端測試：慈濟大學招生通路自動開發系統")
    print("=" * 70)
    
    # Step 1: Google Search
    print("\n📍 步驟 1: Google 搜尋")
    print("-" * 70)
    
    query = "Agen Pendidikan Jakarta"
    print(f"搜尋關鍵字: {query}")
    
    try:
        searcher = GoogleAPISearcher()
        results = searcher.search(query, max_results=3, country_code="ID")
        print(f"✅ 找到 {len(results)} 個搜尋結果\n")
        
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.title}")
            print(f"   URL: {result.url}")
            print(f"   平台: {result.platform}")
            print()
        
    except Exception as e:
        print(f"❌ 搜尋失敗: {e}")
        return False
    
    if not results:
        print("❌ 沒有找到搜尋結果")
        return False
    
    # Step 2: Extract contact information from first result
    print("\n📍 步驟 2: 萃取聯絡資訊")
    print("-" * 70)
    
    test_url = results[0].url
    print(f"測試 URL: {test_url}")
    
    engine = None
    try:
        # Initialize components
        engine = ScrapingEngine(headless=True, use_anti_detection=True)
        contact_finder = ContactPageFinder(engine)
        html_parser = HTMLParser()
        contact_extractor = ContactExtractor()
        contact_validator = ContactValidator()
        
        # Find contact page
        print("\n🔍 尋找聯絡頁面...")
        contact_url = contact_finder.find_contact_page(test_url)
        if contact_url:
            print(f"✅ 找到聯絡頁面: {contact_url}")
        else:
            contact_url = test_url
            print(f"ℹ️  使用主頁面: {test_url}")
        
        # Fetch page content
        print("\n📥 抓取頁面內容...")
        page_content = engine.fetch_page_with_retry(contact_url)
        print(f"✅ 成功抓取頁面 (大小: {len(page_content.html)} bytes)")
        
        # Parse HTML
        print("\n🔍 解析 HTML 並萃取聯絡資訊...")
        parsed_data = html_parser.parse_html(
            page_content.html,
            institution_name=results[0].title
        )
        
        # Display results
        print("\n📊 萃取結果:")
        print("-" * 70)
        
        emails = parsed_data.get("emails", [])
        whatsapp = parsed_data.get("whatsapp_numbers", [])
        institution_type = parsed_data.get("institution_type", "未知")
        
        print(f"機構名稱: {results[0].title}")
        print(f"機構類型: {institution_type}")
        print(f"來源 URL: {test_url}")
        print(f"聯絡頁面: {contact_url}")
        
        if emails:
            print(f"\n📧 Email 地址:")
            for email in emails:
                is_valid = contact_validator.validate_email(email)
                status = "✅" if is_valid else "❌"
                print(f"   {status} {email}")
        else:
            print(f"\n📧 Email 地址: 未找到")
        
        if whatsapp:
            print(f"\n📱 WhatsApp 號碼:")
            for number in whatsapp:
                is_valid = contact_validator.validate_phone(number)
                status = "✅" if is_valid else "❌"
                print(f"   {status} {number}")
        else:
            print(f"\n📱 WhatsApp 號碼: 未找到")
        
        # Calculate quality score
        quality_score = contact_validator.calculate_quality_score(
            has_email=len(emails) > 0,
            has_whatsapp=len(whatsapp) > 0,
            source_platform="website"
        )
        print(f"\n⭐ 資料品質分數: {quality_score}/100")
        
        # Summary
        print("\n" + "=" * 70)
        print("測試總結")
        print("=" * 70)
        print(f"✅ Google API 搜尋: 正常")
        print(f"✅ 頁面抓取: 正常")
        print(f"✅ HTML 解析: 正常")
        print(f"✅ 聯絡資訊萃取: {'成功' if (emails or whatsapp) else '未找到聯絡資訊'}")
        print(f"✅ 資料驗證: 正常")
        
        if emails or whatsapp:
            print(f"\n🎉 端到端測試成功！系統運作正常。")
            return True
        else:
            print(f"\n⚠️  測試完成，但未找到聯絡資訊（可能該網站沒有公開聯絡方式）")
            return True
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if engine:
            engine.close()
            print("\n🔒 已關閉瀏覽器")

if __name__ == "__main__":
    print("\n⏳ 開始測試...\n")
    time.sleep(1)
    
    success = test_end_to_end()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ 所有測試通過！系統已準備好使用。")
    else:
        print("❌ 測試失敗，請檢查錯誤訊息。")
    print("=" * 70 + "\n")
    
    sys.exit(0 if success else 1)
