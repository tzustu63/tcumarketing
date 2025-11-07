# Google Custom Search API 設定指南

## 概述

本系統支援使用 Google Custom Search API 來替代網頁爬蟲，提供更穩定、更快速的搜尋結果。

## 優勢

✅ **更穩定** - 不會被反爬蟲機制偵測或封鎖  
✅ **更快速** - 直接 API 調用，無需載入瀏覽器  
✅ **更準確** - Google 官方搜尋演算法  
✅ **更可靠** - 99.9% 可用性保證  

## 當前狀態

⚠️ **API 未啟用**

根據錯誤訊息，Google Custom Search API 尚未在您的 Google Cloud 專案中啟用。

```
Error: Custom Search API has not been used in project 735686125567 before or it is disabled.
```

## 啟用步驟

### 1. 啟用 Custom Search API

訪問以下 URL 來啟用 API：

```
https://console.developers.google.com/apis/api/customsearch.googleapis.com/overview?project=735686125567
```

或者手動操作：

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 選擇專案 `735686125567`
3. 前往 **APIs & Services** > **Library**
4. 搜尋 "Custom Search API"
5. 點擊 **Enable** 按鈕

### 2. 等待 API 生效

啟用後，請等待 2-5 分鐘讓變更生效。

### 3. 驗證配置

運行測試腳本來驗證 API 是否正常工作：

```bash
docker exec recruitment-worker python test_google_api.py
```

成功的輸出應該類似：

```
✅ Search completed!
Found 5 results

1. 教育代辦機構名稱
   URL: https://example.com
   Platform: website
   Description: ...
```

## 配置信息

當前配置（已在 `.env` 文件中）：

```env
GOOGLE_API_KEY=AIzaSyBOSclexdocQ0AfVb_tJtdMKEqhDuu9fkQ
GOOGLE_CSE_ID=72885fa4f2a474d08
```

## 使用限制

### 免費配額
- **每日免費額度**: 100 次搜尋/天
- **每次請求**: 最多 10 個結果
- **總計最多**: 100 個結果（需要 10 次 API 調用）

### 付費方案
如果需要更多配額：
- **價格**: $5 USD / 1,000 次搜尋
- **每日上限**: 10,000 次搜尋/天

詳情請參考：https://developers.google.com/custom-search/v1/overview#pricing

## 備援機制

如果 Google API 不可用或失敗，系統會自動回退到網頁爬蟲方法：

```python
# 優先使用 API
if settings.GOOGLE_API_KEY and settings.GOOGLE_CSE_ID:
    try:
        results = api_searcher.search(query)
    except Exception:
        # 自動回退到網頁爬蟲
        results = google_scraper.search_google(query)
```

## 監控和日誌

系統會記錄 API 使用情況：

```
🔍 Attempting Google Custom Search API (ID) for: Agen Pendidikan Jakarta
✅ Found 10 results from Google API
```

或者在失敗時：

```
⚠️ Google API search failed: 403 Forbidden
📝 Falling back to web scraping method
```

## 故障排除

### 問題 1: 403 Forbidden Error

**原因**: API 未啟用或 API Key 無效

**解決方案**:
1. 確認 API 已在 Google Cloud Console 中啟用
2. 檢查 API Key 是否正確
3. 確認 API Key 有權限訪問 Custom Search API

### 問題 2: 400 Bad Request

**原因**: CSE ID 不正確

**解決方案**:
1. 前往 [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. 確認 CSE ID 是否正確
3. 更新 `.env` 文件中的 `GOOGLE_CSE_ID`

### 問題 3: 429 Too Many Requests

**原因**: 超過配額限制

**解決方案**:
1. 等待配額重置（每日 00:00 UTC）
2. 考慮升級到付費方案
3. 系統會自動回退到網頁爬蟲

## 相關資源

- [Google Custom Search API 文檔](https://developers.google.com/custom-search/v1/overview)
- [Programmable Search Engine](https://programmablesearchengine.google.com/)
- [Google Cloud Console](https://console.cloud.google.com/)
- [API 定價](https://developers.google.com/custom-search/v1/overview#pricing)

## 聯絡支援

如果遇到問題，請檢查：
1. API 是否已啟用
2. API Key 和 CSE ID 是否正確
3. 配額是否充足
4. 查看系統日誌獲取詳細錯誤信息

```bash
# 查看 Worker 日誌
docker-compose logs worker --tail 50

# 查看 API 日誌
docker-compose logs api --tail 50
```
