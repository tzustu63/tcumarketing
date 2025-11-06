# Railway 部署指南

## 可行性分析

### ✅ 可以部署
是的，這個系統可以部署到 Railway，但需要一些調整和配置。

## 系統架構分析

### 當前架構（Docker Compose）
```
1. PostgreSQL 資料庫
2. Redis 快取/訊息佇列
3. FastAPI 後端 (API)
4. Celery Worker (爬蟲任務)
5. Celery Beat (定時任務)
6. React 前端
```

### Railway 部署架構
Railway 支援多服務部署，每個服務需要單獨配置。

## Railway 部署方案

### 方案 A: 完整部署（推薦）

#### 服務配置

**1. PostgreSQL 資料庫**
- 使用 Railway 的 PostgreSQL 插件
- 自動提供連線 URL
- 包含在免費額度中

**2. Redis**
- 使用 Railway 的 Redis 插件
- 自動提供連線 URL
- 包含在免費額度中

**3. Backend API**
- 部署 FastAPI 應用
- 使用 `backend/Dockerfile`
- 啟動命令: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**4. Celery Worker**
- 部署 Worker 服務
- 使用相同的 `backend/Dockerfile`
- 啟動命令: `celery -A app.celery_app worker --loglevel=info --concurrency=4`

**5. Celery Beat**
- 部署 Beat 服務
- 使用相同的 `backend/Dockerfile`
- 啟動命令: `celery -A app.celery_app beat --loglevel=info`

**6. Frontend**
- 部署 React 應用
- 使用 `frontend/Dockerfile`
- 或使用 Vercel/Netlify 部署前端（更好的選擇）

### 方案 B: 簡化部署

**合併服務**:
- API + Worker 合併（不推薦，但可行）
- 使用 Supervisor 或類似工具管理多個進程

## 部署步驟

### 1. 準備工作

#### 創建 Railway 專案
```bash
# 安裝 Railway CLI
npm install -g @railway/cli

# 登入
railway login

# 創建新專案
railway init
```

#### 添加資料庫服務
```bash
# 添加 PostgreSQL
railway add postgresql

# 添加 Redis
railway add redis
```

### 2. 配置環境變數

Railway 會自動提供以下變數：
- `DATABASE_URL` (PostgreSQL)
- `REDIS_URL` (Redis)

需要手動添加：
```bash
# API 配置
CORS_ORIGINS=["https://your-frontend.railway.app"]
LOG_LEVEL=INFO
RATE_LIMIT_ENABLED=true

# Google API (可選)
GOOGLE_API_KEY=your_api_key
GOOGLE_CSE_ID=your_cse_id

# Celery 配置
TASK_MAX_WORKERS=4
TASK_TIMEOUT=300
```

### 3. 創建 railway.json 配置

**backend/railway.json** (API 服務):
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**backend/railway.worker.json** (Worker 服務):
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "celery -A app.celery_app worker --loglevel=info --concurrency=4",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**backend/railway.beat.json** (Beat 服務):
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "celery -A app.celery_app beat --loglevel=info",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 4. 修改 Dockerfile（如果需要）

確保 Dockerfile 適合 Railway：
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式
COPY . .

# Railway 會自動設定 PORT 環境變數
ENV PORT=8000

# 不需要 CMD，Railway 會使用 railway.json 中的 startCommand
```

### 5. 部署命令

```bash
# 部署 API
railway up --service api

# 部署 Worker
railway up --service worker

# 部署 Beat
railway up --service beat
```

## 注意事項和限制

### ⚠️ 重要限制

#### 1. 資源限制
**免費方案**:
- 記憶體: 512MB - 1GB
- CPU: 共享
- 執行時間: 每月 500 小時
- 儲存空間: 1GB

**問題**:
- ❌ Selenium/Playwright 需要大量記憶體（每個實例 ~200-300MB）
- ❌ 10 個 Workers 可能超過記憶體限制
- ❌ 瀏覽器自動化在容器中可能不穩定

**解決方案**:
- 減少 Worker 數量到 2-4
- 優先使用 Google Custom Search API（不需要瀏覽器）
- 升級到付費方案

#### 2. 網頁爬蟲限制
**問題**:
- Railway 可能限制出站連線
- 某些網站可能封鎖 Railway 的 IP
- Selenium/Playwright 在容器中可能不穩定

**解決方案**:
- 使用 Google Custom Search API
- 使用代理服務
- 考慮使用專門的爬蟲服務（ScrapingBee, Apify）

#### 3. 持久化儲存
**問題**:
- Railway 的檔案系統是臨時的
- 重啟後檔案會丟失

**解決方案**:
- 使用 Railway 的 Volume 功能
- 或使用 S3/Cloudinary 儲存匯出檔案

#### 4. 定時任務
**問題**:
- Celery Beat 需要持續運行
- 會佔用一個服務槽位

**解決方案**:
- 使用 Railway 的 Cron Jobs（如果支援）
- 或保持 Beat 服務運行

### ✅ 優點

1. **簡單部署**: 一鍵部署，自動 CI/CD
2. **自動擴展**: 可以根據需求擴展
3. **內建資料庫**: PostgreSQL 和 Redis 開箱即用
4. **免費額度**: 適合測試和小規模使用
5. **HTTPS**: 自動提供 SSL 證書

### ❌ 缺點

1. **記憶體限制**: 免費方案記憶體有限
2. **爬蟲限制**: 瀏覽器自動化可能不穩定
3. **成本**: 大規模使用需要付費
4. **IP 限制**: 可能被某些網站封鎖

## 成本估算

### 免費方案
- **限制**: 500 小時/月，512MB 記憶體
- **適合**: 測試、開發、小規模使用
- **成本**: $0

### Hobby 方案
- **限制**: $5/月/服務
- **記憶體**: 最多 8GB
- **適合**: 小型生產環境
- **成本**: ~$25-30/月（5-6 個服務）

### Pro 方案
- **限制**: $20/月/服務
- **記憶體**: 最多 32GB
- **適合**: 中大型生產環境
- **成本**: ~$100-120/月

## 替代方案

### 1. Render.com
- 類似 Railway
- 更好的免費方案
- 支援 Background Workers

### 2. Fly.io
- 更適合容器化應用
- 更好的資源控制
- 支援多區域部署

### 3. DigitalOcean App Platform
- 固定價格
- 更可預測的成本
- 更好的資源配置

### 4. 自建 VPS
- 完全控制
- 更便宜（長期）
- 需要自己維護

**推薦**: DigitalOcean Droplet ($12/月) + Docker Compose

### 5. Heroku
- 類似 Railway
- 更成熟的平台
- 但價格較高

## 推薦部署策略

### 階段 1: 測試部署（Railway 免費方案）
```
- PostgreSQL (Railway 插件)
- Redis (Railway 插件)
- API (1 個服務)
- Worker (1 個服務，2 並行)
- Beat (1 個服務)
```

**限制**:
- 減少 Worker 數量
- 使用 Google API 而非瀏覽器爬蟲
- 每月 500 小時限制

### 階段 2: 小規模生產（Railway Hobby）
```
- 升級到 Hobby 方案
- 增加 Worker 數量到 4
- 添加監控和日誌
```

### 階段 3: 大規模生產（VPS 或雲端）
```
- 遷移到 DigitalOcean/AWS/GCP
- 使用 Kubernetes 或 Docker Swarm
- 添加負載平衡和自動擴展
```

## 部署檢查清單

### 準備階段
- [ ] 確認所有環境變數
- [ ] 測試 Google Custom Search API
- [ ] 準備資料庫遷移腳本
- [ ] 配置 CORS 設定
- [ ] 準備監控和日誌

### 部署階段
- [ ] 創建 Railway 專案
- [ ] 添加 PostgreSQL 和 Redis
- [ ] 部署 API 服務
- [ ] 部署 Worker 服務
- [ ] 部署 Beat 服務
- [ ] 執行資料庫遷移
- [ ] 測試 API 端點
- [ ] 測試任務執行

### 驗證階段
- [ ] 創建測試任務
- [ ] 驗證爬蟲功能
- [ ] 驗證資料儲存
- [ ] 驗證定時任務
- [ ] 檢查日誌和錯誤
- [ ] 效能測試

## 總結

### 可以部署到 Railway？
**是的**，但有條件：

✅ **適合 Railway 的情況**:
- 小規模使用（每天 < 100 個任務）
- 主要使用 Google API（不用瀏覽器）
- 測試和開發環境
- 願意付費升級

❌ **不適合 Railway 的情況**:
- 大量使用瀏覽器爬蟲
- 需要大量並行任務（> 10 workers）
- 需要穩定的 IP 地址
- 預算有限但需求大

### 建議
1. **測試階段**: 使用 Railway 免費方案測試
2. **小規模**: Railway Hobby 方案 ($25-30/月)
3. **大規模**: 遷移到 VPS 或雲端平台

### 最佳選擇
對於這個爬蟲系統，我建議：
- **開發/測試**: Railway 免費方案
- **生產環境**: DigitalOcean Droplet ($12/月) + Docker Compose

這樣可以獲得更好的效能和更低的成本。

