# Railway 快速參考卡

## 🎯 專案資訊

```bash
專案 Token: 5ff08d2d-64e7-44f0-ab91-d0f28adcf213
專案名稱: TCU Marketing Auto Scraper
```

---

## ⚡ 最常用指令

### 1. 設定連接

```bash
export RAILWAY_TOKEN=5ff08d2d-64e7-44f0-ab91-d0f28adcf213
```

### 2. 查看服務狀態

```bash
./railway-quick-commands.sh status
```

### 3. 查看 Worker 日誌

```bash
./railway-quick-commands.sh logs-worker
```

### 4. 重新部署 Worker

```bash
./railway-quick-commands.sh deploy-worker
```

### 5. 檢查 Worker 環境變數

```bash
./railway-quick-commands.sh vars-worker
```

---

## 🔴 Celery Worker 連接問題？

### 快速診斷

```bash
# 1. 檢查環境變數
./railway-quick-commands.sh vars-worker | grep REDIS_URL

# 2. 查看錯誤日誌
./railway-quick-commands.sh logs-worker

# 3. 重新部署
./railway-quick-commands.sh deploy-worker
```

### 完整解決方案

👉 查看 [RAILWAY_CELERY_TROUBLESHOOTING.md](./RAILWAY_CELERY_TROUBLESHOOTING.md)

**最常見問題**：Worker 服務沒有連結到 Redis

**解決方法**：
1. 進入 Railway → Worker 服務 → Variables
2. 點擊 **+ New Variable** → **Reference Variable**
3. 選擇 **Redis** 服務
4. 點擊 **Deploy** 重新部署

---

## 📋 所有可用指令

```bash
./railway-quick-commands.sh help
```

### 查看日誌
```bash
logs-api          # API 服務日誌
logs-worker       # Worker 服務日誌
logs-beat         # Beat 服務日誌
logs-frontend     # Frontend 服務日誌
```

### 部署管理
```bash
deploy-api        # 重新部署 API
deploy-worker     # 重新部署 Worker
deploy-beat       # 重新部署 Beat
deploy-frontend   # 重新部署 Frontend
deploy-all        # 重新部署所有服務
```

### 環境變數
```bash
vars-api          # 查看 API 環境變數
vars-worker       # 查看 Worker 環境變數
vars-beat         # 查看 Beat 環境變數
```

### 其他
```bash
status            # 查看所有服務狀態
migrate           # 執行資料庫遷移
shell             # 開啟遠端 shell
```

---

## 🛠️ 原生 Railway CLI 指令

如果需要更多控制，可以直接使用 Railway CLI：

```bash
# 設定 token
export RAILWAY_TOKEN=5ff08d2d-64e7-44f0-ab91-d0f28adcf213

# 查看狀態
railway status

# 查看日誌（即時）
railway logs --service tcu-worker --follow

# 執行指令
railway run --service tcu-api alembic upgrade head

# 查看環境變數
railway variables --service tcu-worker

# 重新部署
railway up --service tcu-worker
```

更多詳細資訊 → [RAILWAY_CLI_USAGE.md](./RAILWAY_CLI_USAGE.md)

---

## 📚 相關文件

| 文件 | 用途 |
|------|------|
| [RAILWAY_SETUP_GUIDE.md](./RAILWAY_SETUP_GUIDE.md) | 完整部署指南 |
| [RAILWAY_CLI_USAGE.md](./RAILWAY_CLI_USAGE.md) | CLI 詳細使用說明 |
| [RAILWAY_CELERY_TROUBLESHOOTING.md](./RAILWAY_CELERY_TROUBLESHOOTING.md) | Worker 故障排除 |
| [ENV_VARIABLES.md](./ENV_VARIABLES.md) | 環境變數說明 |

---

## 🚨 緊急狀況

### Worker 完全無回應

```bash
# 1. 檢查狀態
./railway-quick-commands.sh status

# 2. 查看最近日誌
./railway-quick-commands.sh logs-worker

# 3. 強制重新部署
./railway-quick-commands.sh deploy-worker

# 4. 等待 2-3 分鐘後檢查
./railway-quick-commands.sh logs-worker
```

### 資料庫連接失敗

```bash
# 檢查 DATABASE_URL
./railway-quick-commands.sh vars-api | grep DATABASE_URL

# 如果沒有，在 Railway 網頁上連結 PostgreSQL
```

### Redis 連接失敗

```bash
# 檢查 REDIS_URL
./railway-quick-commands.sh vars-worker | grep REDIS_URL

# 如果沒有，在 Railway 網頁上連結 Redis
```

---

**快速求助**：在所有 Railway 相關文件中搜尋關鍵字

```bash
grep -r "你的關鍵字" RAILWAY_*.md
```

---

**列印此頁**：保存為桌面快速參考！

**最後更新**: 2025-11-07

