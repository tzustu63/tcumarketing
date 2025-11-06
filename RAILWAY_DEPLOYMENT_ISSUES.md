# Railway 部署問題分析

## 實際會遇到的問題

### 🔴 嚴重問題（會導致失敗）

#### 1. Selenium/Playwright 無法運行
**問題**:
```python
# backend/app/scraper/scraping_engine.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
```

**為什麼會失敗**:
- Railway 容器沒有安裝 Chrome/Chromium
- 即使安裝，也需要大量依賴（~500MB）
- 記憶體不足（Chrome 需要 200-300MB）
- 無頭模式在容器中不穩定

**錯誤訊息**:
```
selenium.common.exceptions.WebDriverException: 
Message: 'chromedriver' executable needs to be in PATH
```

**影響**:
- ❌ 無法使用 Google 網頁爬蟲
- ❌ 無法爬取 Facebook/Instagram
- ❌ 大部分爬蟲功能失效

**解決方案**:
```python
# 選項 1: 只使用 Google Custom Search API
if settings.GOOGLE_API_KEY and settings.GOOGLE_CSE_ID:
    # 使用 API，不需要瀏覽器
    use_api = True
else:
    # 無法使用爬蟲
    raise Exception("Google API required for Railway deployment")

# 選項 2: 使用外部爬蟲服務
# - ScrapingBee
# - Apify
# - Bright Data
```

#### 2. 記憶體限制
**問題**:
```yaml
# docker-compose.yml
worker:
  command: celery -A app.celery_app worker --concurrency=10
```

**為什麼會失敗**:
- 免費方案：512MB-1GB 記憶體
- 10 個 Workers：每個 ~120MB = 1.2GB
- PostgreSQL：~100MB
- Redis：~50MB
- 總需求：~1.5-2GB

**錯誤訊息**:
```
MemoryError: Unable to allocate memory
OOMKilled: Container killed due to out of memory
```

**影響**:
- ❌ Worker 容器崩潰
- ❌ 任務執行失敗
- ❌ 系統不穩定

**解決方案**:
```bash
# 減少 Worker 數量
celery -A app.celery_app worker --concurrency=2

# 或升級到付費方案
# Hobby: $5/月/服務 (最多 8GB)
```

#### 3. 多服務部署複雜度
**問題**:
你的系統需要 5 個獨立服務：
```
1. API (FastAPI)
2. Worker (Celery)
3. Beat (Celery Beat)
4. PostgreSQL
5. Redis
```

**為什麼會複雜**:
- 每個服務需要單獨配置
- 需要正確設定環境變數
- 服務間需要正確連接
- 部署順序很重要

**可能的錯誤**:
```
# Worker 找不到資料庫
sqlalchemy.exc.OperationalError: could not connect to server

# Worker 找不到 Redis
redis.exceptions.ConnectionError: Error connecting to Redis

# 環境變數不一致
KeyError: 'DATABASE_URL'
```

**影響**:
- ⚠️ 部署時間長
- ⚠️ 容易出錯
- ⚠️ 難以除錯

### 🟡 中等問題（可以解決但麻煩）

#### 4. 檔案儲存問題
**問題**:
```python
# backend/app/services/export_service.py
export_path = "/app/exports/contacts.xlsx"
```

**為什麼會有問題**:
- Railway 的檔案系統是臨時的
- 容器重啟後檔案會消失
- 無法在服務間共享檔案

**影響**:
- ⚠️ 匯出的 Excel 檔案會丟失
- ⚠️ 無法下載歷史匯出

**解決方案**:
```python
# 選項 1: 使用 S3/Cloudinary
import boto3
s3 = boto3.client('s3')
s3.upload_file(local_file, bucket, key)

# 選項 2: 使用 Railway Volumes
# 在 Railway 設定中添加 Volume

# 選項 3: 直接返回檔案流，不儲存
return StreamingResponse(
    io.BytesIO(excel_data),
    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
```

#### 5. 環境變數管理
**問題**:
```bash
# .env 文件
DATABASE_URL=postgresql://user:pass@db:5432/recruitment
REDIS_URL=redis://redis:6379/0
```

**為什麼會有問題**:
- Railway 自動生成的 URL 格式不同
- 服務名稱不是 `db` 或 `redis`
- 需要手動配置所有環境變數

**Railway 提供的格式**:
```bash
DATABASE_URL=postgresql://postgres:***@containers-us-west-123.railway.app:5432/railway
REDIS_URL=redis://default:***@containers-us-west-456.railway.app:6379
```

**影響**:
- ⚠️ 需要更新所有環境變數
- ⚠️ 本地和生產環境配置不同
- ⚠️ 容易配置錯誤

**解決方案**:
```python
# 使用 Railway 自動注入的環境變數
import os

DATABASE_URL = os.getenv("DATABASE_URL")  # Railway 自動提供
REDIS_URL = os.getenv("REDIS_URL")        # Railway 自動提供

# 或在 Railway 設定中手動添加
```

#### 6. 建置時間和大小
**問題**:
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y \
    gcc postgresql-client chromium chromium-driver
```

**為什麼會有問題**:
- 安裝 Chromium：~500MB
- 安裝所有依賴：~1GB
- 建置時間：5-10 分鐘
- 超過 Railway 免費方案限制

**影響**:
- ⚠️ 部署很慢
- ⚠️ 可能超時
- ⚠️ 佔用大量儲存空間

**解決方案**:
```dockerfile
# 移除不必要的依賴
FROM python:3.11-slim
RUN apt-get update && apt-get install -y \
    gcc postgresql-client \
    && rm -rf /var/lib/apt/lists/*
# 不安裝 Chromium
```

### 🟢 小問題（容易解決）

#### 7. CORS 配置
**問題**:
```python
# backend/app/main.py
CORS_ORIGINS=["http://localhost:3000"]
```

**為什麼需要更新**:
- Railway 會提供隨機域名
- 前端和後端域名不同
- 需要允許跨域請求

**解決方案**:
```python
CORS_ORIGINS = [
    "http://localhost:3000",
    "https://your-frontend.railway.app",
    "https://*.railway.app"  # 允許所有 Railway 子域名
]
```

#### 8. 資料庫遷移
**問題**:
- 需要在部署後執行 Alembic 遷移
- Railway 沒有自動遷移機制

**解決方案**:
```bash
# 選項 1: 手動執行
railway run alembic upgrade head

# 選項 2: 在啟動腳本中執行
# start.sh
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

#### 9. 日誌和監控
**問題**:
- 無法直接查看 Worker 日誌
- 難以除錯任務失敗

**解決方案**:
```python
# 使用 Railway 的日誌
import logging
logging.basicConfig(level=logging.INFO)

# 或使用外部服務
# - Sentry (錯誤追蹤)
# - LogDNA (日誌管理)
```

## 部署前必須解決的問題

### 🔴 必須修改（否則無法運行）

1. **移除 Selenium/Playwright 依賴**
   ```bash
   # requirements.txt
   # selenium==4.15.2  # 註解掉
   # playwright==1.40.0  # 註解掉
   ```

2. **只使用 Google Custom Search API**
   ```python
   # 確保設定了 API Key
   GOOGLE_API_KEY=your_key
   GOOGLE_CSE_ID=your_cse_id
   ```

3. **減少 Worker 數量**
   ```bash
   # 從 10 改為 2-4
   celery -A app.celery_app worker --concurrency=2
   ```

### 🟡 建議修改（提升穩定性）

4. **使用 S3 儲存匯出檔案**
5. **添加健康檢查端點**
6. **配置正確的 CORS**
7. **設定環境變數**

### 🟢 可選修改（改善體驗）

8. **添加 Sentry 錯誤追蹤**
9. **使用 Redis 持久化**
10. **添加監控儀表板**

## 成本估算

### 免費方案（不推薦）
```
限制:
- 500 小時/月
- 512MB 記憶體
- 1GB 儲存

問題:
- 5 個服務 = 3,600 小時/月 (超過限制)
- 記憶體不足
- 無法運行瀏覽器

結論: ❌ 不可行
```

### Hobby 方案（最低可行）
```
成本: $5/月/服務 × 5 = $25/月

配置:
- API: $5/月
- Worker: $5/月 (2 並行)
- Beat: $5/月
- PostgreSQL: $5/月
- Redis: $5/月

限制:
- 最多 8GB 記憶體
- 仍無法使用瀏覽器爬蟲
- 只能用 Google API

結論: ⚠️ 可行但功能受限
```

### Pro 方案（完整功能）
```
成本: $20/月/服務 × 5 = $100/月

配置:
- 可以安裝 Chromium
- 足夠記憶體運行瀏覽器
- 可以增加 Worker 數量

結論: ✅ 可行但昂貴
```

## 推薦的替代方案

### 方案 1: Railway (API only) + 外部爬蟲服務
```
成本: $25/月 (Railway) + $29/月 (ScrapingBee)
優點: 穩定、可靠
缺點: 依賴外部服務
```

### 方案 2: DigitalOcean Droplet
```
成本: $12/月
優點: 完全控制、便宜
缺點: 需要自己維護
推薦: ✅ 最佳選擇
```

### 方案 3: Render.com
```
成本: 類似 Railway
優點: 更好的免費方案
缺點: 類似限制
```

## 總結

### 會遇到的主要問題：

1. **🔴 Selenium/Playwright 無法運行** - 最嚴重
2. **🔴 記憶體不足** - 會導致崩潰
3. **🟡 多服務配置複雜** - 容易出錯
4. **🟡 檔案儲存問題** - 需要額外配置
5. **🟡 成本高** - 至少 $25/月

### 我的建議：

**不要部署到 Railway**，原因：
- 瀏覽器爬蟲無法運行
- 成本高（$25-100/月）
- 配置複雜
- 功能受限

**改用 DigitalOcean Droplet**：
- 成本：$12/月
- 完整功能
- 完全控制
- 使用現有的 Docker Compose

需要我幫你準備 DigitalOcean 部署指南嗎？

