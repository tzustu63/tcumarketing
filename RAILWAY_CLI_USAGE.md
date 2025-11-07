# Railway CLI 使用指南

## 📋 專案資訊

- **專案 Token**: `5ff08d2d-64e7-44f0-ab91-d0f28adcf213`
- **服務列表**:
  - `tcu-api` - FastAPI 應用程式
  - `tcu-worker` - Celery Worker
  - `tcu-beat` - Celery Beat（定時任務）
  - `tcu-frontend` - React 前端

---

## 🚀 快速開始

### 1. 安裝 Railway CLI

```bash
# macOS (使用 Homebrew)
brew install railway

# 或使用 npm
npm install -g @railway/cli

# 驗證安裝
railway --version
```

### 2. 登入 Railway

```bash
railway login
```

這會開啟瀏覽器進行身份驗證。

### 3. 連接到專案

#### 方式 A：使用專案 Token（推薦）

```bash
# 設定環境變數
export RAILWAY_TOKEN=5ff08d2d-64e7-44f0-ab91-d0f28adcf213

# 驗證連接
railway status
```

#### 方式 B：使用互動式連結

```bash
railway link
# 然後從列表中選擇您的專案
```

---

## 🛠️ 常用指令

### 查看服務狀態

```bash
railway status
```

輸出範例：
```
✓ Connected to project: TCU Marketing
✓ Current environment: production

Services:
  tcu-api       ✓ Active
  tcu-worker    ✓ Active
  tcu-beat      ✓ Active
  tcu-frontend  ✓ Active
```

### 查看服務日誌

```bash
# API 日誌（即時）
railway logs --service tcu-api

# Worker 日誌
railway logs --service tcu-worker

# Beat 日誌
railway logs --service tcu-beat

# 查看最近 100 行
railway logs --service tcu-worker --lines 100
```

### 執行資料庫遷移

```bash
railway run --service tcu-api alembic upgrade head
```

### 在遠端執行指令

```bash
# 檢查 Python 版本
railway run --service tcu-api python --version

# 執行 Celery 檢查
railway run --service tcu-worker celery -A app.celery_app inspect ping

# 查看已註冊的任務
railway run --service tcu-worker celery -A app.celery_app inspect registered

# 開啟互動式 shell
railway run --service tcu-api bash
```

### 查看環境變數

```bash
# 查看所有環境變數
railway variables --service tcu-worker

# 檢查特定變數
railway variables --service tcu-worker | grep REDIS_URL
railway variables --service tcu-worker | grep DATABASE_URL
```

### 設定環境變數（通過 CLI）

```bash
# 設定單個變數
railway variables --service tcu-worker set LOG_LEVEL=DEBUG

# 刪除變數
railway variables --service tcu-worker delete OLD_VAR
```

### 重新部署服務

```bash
# 觸發重新部署
railway up --service tcu-worker

# 部署並查看日誌
railway up --service tcu-worker && railway logs --service tcu-worker
```

---

## 🔧 故障排除指令

### 檢查 Worker 連接問題

```bash
# 1. 查看 Worker 環境變數
railway variables --service tcu-worker | grep -E "REDIS_URL|DATABASE_URL"

# 2. 查看 Worker 日誌
railway logs --service tcu-worker --lines 100

# 3. 檢查 Worker 狀態
railway run --service tcu-worker celery -A app.celery_app inspect ping

# 4. 如果沒有回應，重新部署
railway up --service tcu-worker
```

### 檢查 Redis 連接

```bash
# 在 API 服務中測試 Redis 連接
railway run --service tcu-api python -c "
import os
from redis import Redis
redis_url = os.getenv('REDIS_URL')
print(f'Redis URL: {redis_url}')
r = Redis.from_url(redis_url)
print(f'Redis Ping: {r.ping()}')
"
```

### 檢查資料庫連接

```bash
# 測試資料庫連接
railway run --service tcu-api python -c "
import os
from sqlalchemy import create_engine
db_url = os.getenv('DATABASE_URL')
print(f'Database URL: {db_url[:30]}...')
engine = create_engine(db_url)
with engine.connect() as conn:
    print('Database connected!')
"
```

### 查看 Celery Worker 狀態

```bash
# 查看活動 Worker
railway run --service tcu-worker celery -A app.celery_app inspect active

# 查看已註冊的任務
railway run --service tcu-worker celery -A app.celery_app inspect registered

# 查看 Worker 統計
railway run --service tcu-worker celery -A app.celery_app inspect stats
```

---

## 📦 使用快速指令腳本

專案包含 `railway-quick-commands.sh` 腳本，簡化常用操作：

```bash
# 查看所有可用指令
./railway-quick-commands.sh help

# 執行資料庫遷移
./railway-quick-commands.sh migrate

# 查看 Worker 日誌
./railway-quick-commands.sh logs-worker

# 重新部署 Worker
./railway-quick-commands.sh deploy-worker

# 查看 Worker 環境變數
./railway-quick-commands.sh vars-worker

# 查看所有服務狀態
./railway-quick-commands.sh status
```

---

## 🔐 環境變數管理

### 必要的環境變數

#### API 服務 (`tcu-api`)
- `DATABASE_URL` - PostgreSQL 連接（自動注入）
- `REDIS_URL` - Redis 連接（自動注入）
- `SERVICE_ROLE=api`
- `PORT=8000`
- `GOOGLE_API_KEY` - Google API 金鑰
- `GOOGLE_CSE_ID` - Google Custom Search Engine ID

#### Worker 服務 (`tcu-worker`)
- `DATABASE_URL` - PostgreSQL 連接（自動注入）
- `REDIS_URL` - Redis 連接（自動注入）
- `SERVICE_ROLE=worker`
- `TASK_MAX_WORKERS=8`
- `GOOGLE_API_KEY` - Google API 金鑰
- `GOOGLE_CSE_ID` - Google Custom Search Engine ID

#### Beat 服務 (`tcu-beat`)
- `DATABASE_URL` - PostgreSQL 連接（自動注入）
- `REDIS_URL` - Redis 連接（自動注入）
- `SERVICE_ROLE=beat`

### 檢查環境變數是否正確設定

```bash
# 檢查 Worker 環境變數
./railway-quick-commands.sh vars-worker

# 或使用 Railway CLI
railway variables --service tcu-worker
```

---

## 🚨 常見問題

### Q: 執行指令時出現 "No project linked"

**解決方案**：
```bash
export RAILWAY_TOKEN=5ff08d2d-64e7-44f0-ab91-d0f28adcf213
railway status
```

### Q: Worker 無法連接到 Redis

**診斷步驟**：
```bash
# 1. 確認 REDIS_URL 存在
railway variables --service tcu-worker | grep REDIS_URL

# 2. 查看詳細錯誤日誌
railway logs --service tcu-worker --lines 100

# 3. 如果 REDIS_URL 不存在，在 Railway 網頁上添加
```

**解決方案**：請參考 [RAILWAY_CELERY_TROUBLESHOOTING.md](./RAILWAY_CELERY_TROUBLESHOOTING.md)

### Q: 如何查看即時日誌？

```bash
# 使用 --follow 或 -f 標記
railway logs --service tcu-worker --follow

# 或簡寫
railway logs -s tcu-worker -f
```

### Q: 如何在本地使用 Railway 的環境變數？

```bash
# 執行本地指令但使用 Railway 環境變數
railway run --service tcu-api python script.py

# 或進入 shell
railway run --service tcu-api bash
```

---

## 📚 更多資源

- [Railway 官方文件](https://docs.railway.app/)
- [Railway CLI 參考](https://docs.railway.app/develop/cli)
- [專案部署指南](./RAILWAY_SETUP_GUIDE.md)
- [Celery 故障排除](./RAILWAY_CELERY_TROUBLESHOOTING.md)

---

## 💡 進階技巧

### 一鍵部署所有服務

```bash
for service in tcu-api tcu-worker tcu-beat tcu-frontend; do
    echo "Deploying $service..."
    railway up --service $service
done
```

### 監控多個服務日誌

在不同的終端視窗中執行：

```bash
# 終端 1
railway logs --service tcu-api -f

# 終端 2
railway logs --service tcu-worker -f

# 終端 3
railway logs --service tcu-beat -f
```

### 備份環境變數

```bash
# 備份所有服務的環境變數
railway variables --service tcu-api > vars-api.txt
railway variables --service tcu-worker > vars-worker.txt
railway variables --service tcu-beat > vars-beat.txt
```

### 快速健康檢查

```bash
#!/bin/bash
echo "=== Health Check ==="

echo -n "API: "
railway run --service tcu-api curl -s http://localhost:8000/health && echo "✓" || echo "✗"

echo -n "Worker: "
railway run --service tcu-worker celery -A app.celery_app inspect ping && echo "✓" || echo "✗"

echo -n "Database: "
railway run --service tcu-api alembic current && echo "✓" || echo "✗"
```

---

**最後更新**: 2025-11-07
**專案**: TCU Marketing Auto Scraper
**Railway Project ID**: 5ff08d2d-64e7-44f0-ab91-d0f28adcf213

