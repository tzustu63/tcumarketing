# 效能優化實施指南

## 📋 快速開始

根據效能分析報告，以下是優化程式的具體實施步驟。

## ✅ 已完成的優化

### 1. Celery Rate Limit 已優化
- ✅ `backend/app/celery_app.py` 中的 rate limit 已提高
- Google 搜尋任務: 10/m → 30/m
- 網站萃取任務: 30/m → 60/m
- 社交媒體萃取任務: 20/m → 40/m

## 🔧 需要手動調整的設定

### 步驟 1: 調整環境變數

編輯專案根目錄的 `.env` 文件，添加或修改以下設定：

```bash
# ============================================
# 爬蟲延遲設定（降低延遲以提高速度）
# ============================================
SCRAPING_MIN_DELAY=1
SCRAPING_MAX_DELAY=2
RATE_LIMIT_MIN_REQUEST_INTERVAL=1.0

# ============================================
# Rate Limiting 設定（提高限制以加快處理）
# ============================================
RATE_LIMIT_ENABLED=true
RATE_LIMIT_MAX_REQUESTS_PER_DOMAIN=20
RATE_LIMIT_DOMAIN_TIME_WINDOW=60
RATE_LIMIT_MAX_REQUESTS_PER_MINUTE=120
RATE_LIMIT_MAX_CONCURRENT_REQUESTS=20

# ============================================
# Worker 配置（增加並行處理能力）
# ============================================
# 注意: 根據伺服器記憶體調整
# 計算公式: (總記憶體MB - 512MB) / 120MB
# 例如 2GB 伺服器: (2048 - 512) / 120 ≈ 12
TASK_MAX_WORKERS=12

# ============================================
# 超時設定（降低超時以加快失敗檢測）
# ============================================
SCRAPING_TIMEOUT=20
```

### 步驟 2: 重啟服務

```bash
# 方法 1: 僅重啟 worker（推薦，影響較小）
docker-compose restart worker

# 方法 2: 完整重啟所有服務
docker-compose down
docker-compose up -d

# 方法 3: 在生產環境（DigitalOcean）
ssh root@your-server-ip
cd /path/to/project
docker-compose restart worker
```

### 步驟 3: 驗證配置

```bash
# 檢查 worker 配置
docker-compose exec worker celery -A app.celery_app inspect stats

# 檢查環境變數
docker-compose exec worker env | grep -E "(SCRAPING|RATE_LIMIT|TASK_MAX)"

# 查看 worker 日誌
docker-compose logs worker --tail 50 -f
```

## 📊 預期改善效果

### 效能改善預估

| 指標 | 優化前 | 優化後 | 改善 |
|------|--------|--------|------|
| 爬取 50 個網站延遲時間 | ~3 分鐘 | ~1 分鐘 | **66% 改善** |
| 50 個萃取任務開始時間 | ~2 分鐘 | ~50 秒 | **58% 改善** |
| 總執行時間 (50 個網站) | ~5-7 分鐘 | ~2-3 分鐘 | **50-60% 改善** |
| 並行處理能力 | 4-10 workers | 12 workers | **20-200% 提升** |

## ⚠️ 注意事項與風險評估

### 風險 1: 被封鎖風險增加
**風險等級**: 🟡 中等

**說明**:
- 降低延遲和提高請求頻率可能被目標網站偵測為機器人行為
- 某些網站可能實施更嚴格的反爬蟲機制

**緩解措施**:
1. 先在小規模測試（10-20 個網站）
2. 監控錯誤率和被封鎖情況
3. 如果被封鎖率 > 1%，調整回較安全的設定
4. 考慮使用 Google Custom Search API 替代網頁爬蟲

**建議設定調整**:
```bash
# 如果遇到被封鎖，可以調整為:
SCRAPING_MIN_DELAY=1.5
SCRAPING_MAX_DELAY=3
RATE_LIMIT_MIN_REQUEST_INTERVAL=1.5
```

### 風險 2: 資源使用增加
**風險等級**: 🟡 中等

**說明**:
- 增加 worker 數量會增加記憶體使用
- 提高並行處理可能增加 CPU 負載

**緩解措施**:
1. 監控記憶體使用情況（應該 < 80%）
2. 監控 CPU 使用情況（應該 < 80%）
3. 根據實際資源調整 worker 數量

**記憶體計算**:
```
總記憶體需求 = 
  PostgreSQL: ~100MB
  Redis: ~50MB
  API: ~100MB
  Worker (每個): ~120MB
  系統保留: ~300MB

範例（12 workers）:
總需求 = 100 + 50 + 100 + (12 × 120) + 300 = 1990MB ≈ 2GB
```

### 風險 3: 資料庫負載增加
**風險等級**: 🟢 低

**說明**:
- 更多並行任務可能增加資料庫查詢頻率
- PostgreSQL 預設連接池應該足夠處理

**緩解措施**:
1. 監控資料庫連接數
2. 如果遇到連接數限制，調整 `pool_size` 設定

## 📈 監控指標

優化後應該監控以下指標：

### 1. 效能指標
- ✅ 任務執行時間（應該降低）
- ✅ 任務完成率（應該維持或提高）
- ✅ 平均每任務處理時間（應該降低）

### 2. 錯誤指標
- ⚠️ 錯誤率（應該 < 5%）
- ⚠️ 被封鎖率（應該 < 1%）
- ⚠️ 超時錯誤率（應該 < 2%）

### 3. 資源指標
- ⚠️ 記憶體使用率（應該 < 80%）
- ⚠️ CPU 使用率（應該 < 80%）
- ⚠️ 資料庫連接數（應該 < 最大連接數的 80%）

### 監控命令

```bash
# 檢查任務執行情況
docker-compose exec worker celery -A app.celery_app inspect active
docker-compose exec worker celery -A app.celery_app inspect stats

# 檢查資源使用
docker stats

# 檢查資料庫連接
docker-compose exec db psql -U user -d recruitment -c "SELECT count(*) FROM pg_stat_activity;"

# 查看錯誤日誌
docker-compose logs worker | grep -i error | tail -20
```

## 🔄 回滾步驟

如果優化後出現問題，可以快速回滾：

### 回滾設定值

編輯 `.env` 文件，恢復原始值：

```bash
# 恢復原始延遲設定
SCRAPING_MIN_DELAY=2
SCRAPING_MAX_DELAY=5
RATE_LIMIT_MIN_REQUEST_INTERVAL=2.0

# 恢復原始 Rate Limiting 設定
RATE_LIMIT_MAX_REQUESTS_PER_DOMAIN=10
RATE_LIMIT_MAX_REQUESTS_PER_MINUTE=60
RATE_LIMIT_MAX_CONCURRENT_REQUESTS=10

# 恢復原始 Worker 數量
TASK_MAX_WORKERS=4
```

然後重啟服務：
```bash
docker-compose restart worker
```

### 回滾 Celery Rate Limit

編輯 `backend/app/celery_app.py`，恢復原始值：

```python
task_annotations={
    'scraping_tasks.scrape_google_task': {
        'rate_limit': '10/m',
    },
    'scraping_tasks.extract_website_task': {
        'rate_limit': '30/m',
    },
    'scraping_tasks.extract_social_task': {
        'rate_limit': '20/m',
    },
}
```

## 🚀 進一步優化建議

### 1. 使用 Google Custom Search API
**優勢**: 
- 完全避免網頁爬蟲延遲
- 更穩定的搜尋結果
- 無被封鎖風險

**實施**:
```bash
# 在 .env 中設定
GOOGLE_API_KEY=your_api_key
GOOGLE_CSE_ID=your_cse_id
```

### 2. 實現請求快取
**優勢**:
- 避免重複爬取相同網站
- 大幅減少不必要的請求

**實施建議**:
- 使用 Redis 快取已爬取的 URL
- 設定快取過期時間（例如 24 小時）

### 3. 優化資料庫查詢
**優勢**:
- 減少資料庫負載
- 加快查詢速度

**實施建議**:
- 添加適當的資料庫索引
- 使用 `select_related` 或 `joinedload` 優化關聯查詢

### 4. 使用異步請求
**優勢**:
- 對簡單網站可以使用 HTTP 請求而非 Selenium
- 大幅減少資源使用和執行時間

**實施建議**:
- 對不依賴 JavaScript 的網站使用 `httpx` 或 `requests`
- 僅對需要 JavaScript 渲染的網站使用 Selenium

## 📝 檢查清單

優化完成後，請確認：

- [ ] 環境變數已更新
- [ ] Celery rate limit 已更新（已完成）
- [ ] Worker 已重啟
- [ ] 配置已驗證
- [ ] 監控指標已設定
- [ ] 測試任務執行正常
- [ ] 錯誤率在可接受範圍內
- [ ] 資源使用在安全範圍內

## 🆘 問題排查

### 問題 1: Worker 啟動失敗
**可能原因**: Worker 數量過多，記憶體不足

**解決方案**:
```bash
# 降低 worker 數量
TASK_MAX_WORKERS=8

# 重啟
docker-compose restart worker
```

### 問題 2: 任務執行失敗增加
**可能原因**: Rate limit 過高，被目標網站封鎖

**解決方案**:
```bash
# 降低 rate limit 和增加延遲
SCRAPING_MIN_DELAY=1.5
SCRAPING_MAX_DELAY=3
RATE_LIMIT_MAX_REQUESTS_PER_DOMAIN=15
```

### 問題 3: 資料庫連接錯誤
**可能原因**: 並行任務過多，連接池耗盡

**解決方案**:
- 檢查資料庫連接池設定
- 考慮增加 `pool_size` 或 `max_overflow`

## 📞 支援

如果遇到問題，請：
1. 查看 `PERFORMANCE_ANALYSIS.md` 了解詳細分析
2. 檢查日誌: `docker-compose logs worker`
3. 檢查資源使用: `docker stats`
4. 根據錯誤訊息調整設定





