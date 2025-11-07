# Railway 部署設定指南（解決 Railpack 錯誤）

## ⚠️ 重要：多服務專案部署方式

此專案包含多個服務（API、Worker、Beat、Frontend），需要**分別建立 4 個 Railway 服務**，每個服務指向不同的 Dockerfile。

---

## 🚀 正確的部署步驟

### 步驟 1：建立 PostgreSQL 和 Redis

1. 登入 Railway：https://railway.app
2. 點擊 **"New Project"** → **"Provision PostgreSQL"**
3. 再次點擊專案內的 **"+ New"** → **"Database"** → **"Add Redis"**

### 步驟 2：建立 API 服務

1. 在專案中點擊 **"+ New"** → **"GitHub Repo"**
2. 選擇 `tzustu63/tcumarketing`
3. **立即進行以下設定（部署前）**：

#### Settings → General：
- **Service Name**: `tcu-api`
- **Root Directory**: `backend`

#### Settings → Build：
- **Builder**: Docker
- **Dockerfile Path**: `Dockerfile`（相對於 Root Directory）

#### Settings → Deploy：
- **Start Command**: `/app/start.sh`
- **Healthcheck Path**: `/health`

#### Settings → Variables（環境變數）：

**⚠️ 重要：先連結資料庫！**
1. 點擊 **+ New Variable** → **Reference Variable**
2. 選擇 **PostgreSQL** 服務（自動注入 `DATABASE_URL`）
3. 再次點擊 **+ New Variable** → **Reference Variable**
4. 選擇 **Redis** 服務（自動注入 `REDIS_URL`）

然後手動添加以下變數：
```bash
SERVICE_ROLE=api
PORT=8000
UVICORN_RELOAD=false
API_HOST=0.0.0.0
LOG_LEVEL=INFO
GOOGLE_API_KEY=你的金鑰
GOOGLE_CSE_ID=你的CSE_ID
RATE_LIMIT_ENABLED=true
SCRAPING_HEADLESS=true
```

### 步驟 3：建立 Worker 服務

1. 點擊 **"+ New"** → **"GitHub Repo"** → 選擇 `tcumarketing`
2. **立即設定**：

#### Settings → General：
- **Service Name**: `tcu-worker`
- **Root Directory**: `backend`

#### Settings → Build：
- **Builder**: Docker
- **Dockerfile Path**: `Dockerfile`

#### Settings → Variables：

**⚠️ 重要：先連結資料庫！**
1. 點擊 **+ New Variable** → **Reference Variable**
2. 選擇 **PostgreSQL** 服務（自動注入 `DATABASE_URL`）
3. 再次點擊 **+ New Variable** → **Reference Variable**
4. 選擇 **Redis** 服務（自動注入 `REDIS_URL`）

然後手動添加以下變數：
```bash
SERVICE_ROLE=worker
TASK_MAX_WORKERS=8
TASK_TIMEOUT=300
LOG_LEVEL=INFO
GOOGLE_API_KEY=你的金鑰
GOOGLE_CSE_ID=你的CSE_ID
RATE_LIMIT_ENABLED=true
SCRAPING_HEADLESS=true
```

### 步驟 4：建立 Beat 服務

1. 點擊 **"+ New"** → **"GitHub Repo"** → 選擇 `tcumarketing`
2. **立即設定**：

#### Settings → General：
- **Service Name**: `tcu-beat`
- **Root Directory**: `backend`

#### Settings → Build：
- **Builder**: Docker
- **Dockerfile Path**: `Dockerfile`

#### Settings → Variables：

**⚠️ 重要：先連結資料庫！**
1. 點擊 **+ New Variable** → **Reference Variable**
2. 選擇 **PostgreSQL** 服務（自動注入 `DATABASE_URL`）
3. 再次點擊 **+ New Variable** → **Reference Variable**
4. 選擇 **Redis** 服務（自動注入 `REDIS_URL`）

然後手動添加以下變數：
```bash
SERVICE_ROLE=beat
LOG_LEVEL=INFO
```

### 步驟 5：建立 Frontend 服務

1. 點擊 **"+ New"** → **"GitHub Repo"** → 選擇 `tcumarketing`
2. **等待 API 服務部署完成，取得 API URL**
3. **立即設定**：

#### Settings → General：
- **Service Name**: `tcu-frontend`
- **Root Directory**: `frontend`

#### Settings → Build：
- **Builder**: Docker
- **Dockerfile Path**: `Dockerfile`
- **Build Args**（重要！）：
  ```
  REACT_APP_API_URL=https://tcu-api.up.railway.app
  ```

#### Settings → Variables：
```bash
NODE_ENV=production
REACT_APP_API_URL=https://tcu-api.up.railway.app
PORT=3000
```

### 步驟 6：執行資料庫遷移

等所有服務都部署成功後，在本地執行：

```bash
# 安裝 Railway CLI
npm install -g @railway/cli

# 登入
railway login

# 使用專案 token 連接（快速方式）
export RAILWAY_TOKEN=5ff08d2d-64e7-44f0-ab91-d0f28adcf213

# 執行資料庫遷移（指定 API 服務）
railway run --service tcu-api alembic upgrade head
```

或者使用互動式方式：

```bash
# 連接到專案（會列出你的所有專案讓你選擇）
railway link

# 執行資料庫遷移
railway run --service tcu-api alembic upgrade head
```

或者在 Railway 網頁上：
1. 進入 `tcu-api` 服務
2. 點擊 **Settings** → **Deploy**
3. 在 **Custom Start Command** 中暫時輸入：
   ```
   alembic upgrade head && /app/start.sh
   ```
4. 觸發重新部署
5. 部署成功後，移除 `alembic upgrade head &&` 部分

---

## ✅ 檢查清單

完成後，你應該有：

- [ ] PostgreSQL 資料庫（自動注入 `DATABASE_URL`）
- [ ] Redis 資料庫（自動注入 `REDIS_URL`）
- [ ] tcu-api 服務（Root: backend, 環境變數已設定）
- [ ] tcu-worker 服務（Root: backend, 環境變數已設定）
- [ ] tcu-beat 服務（Root: backend, 環境變數已設定）
- [ ] tcu-frontend 服務（Root: frontend, 環境變數已設定）
- [ ] 資料庫遷移已執行

---

## 🔍 常見問題

### Q: 為什麼出現 "Railpack could not determine how to build"？
**A**: 因為沒有設定 **Root Directory**。必須在 Settings → General 中設定：
- Backend 服務：`backend`
- Frontend 服務：`frontend`

### Q: 如何知道 API 的 URL？
**A**: 
1. 進入 `tcu-api` 服務
2. 點擊 **Settings** → **Networking**
3. 點擊 **Generate Domain**
4. 複製這個 URL（例如：`https://tcu-api.up.railway.app`）

### Q: 部署失敗怎麼辦？
**A**: 
1. 點擊服務查看 **Deployments**
2. 點擊失敗的部署查看 **Build Logs** 和 **Deploy Logs**
3. 檢查環境變數是否都設定正確

### Q: Worker 出現 "Celery connection error" 怎麼辦？
**A**: 這是因為 Worker 無法連接到 Redis。請確認：

1. **檢查 Redis 連結**：
   - 進入 Worker 服務 → **Variables** 標籤
   - 確認有 `REDIS_URL` 變數（應該是自動注入的）
   - 如果沒有，點擊 **+ New Variable** → **Reference Variable** → 選擇 **Redis**

2. **手動設定 Redis URL**（如果自動注入失敗）：
   - 進入 Redis 服務，複製 `REDIS_URL` 的值
   - 進入 Worker 服務 → **Variables**
   - 手動添加：
     ```
     REDIS_URL=redis://:password@host:port
     ```

3. **重新部署**：
   - 點擊 **Deployments** → **Deploy** 按鈕
   - 等待重新部署完成

4. **查看日誌確認**：
   - 部署成功後，查看 **Deploy Logs**
   - 應該看到 "Connected to redis://..." 的訊息

---

## 🛠️ Railway CLI 快速指令

專案已包含快速管理腳本 `railway-quick-commands.sh`，方便您管理 Railway 部署：

### 使用方式

```bash
# 查看所有可用指令
./railway-quick-commands.sh help

# 執行資料庫遷移
./railway-quick-commands.sh migrate

# 查看服務日誌
./railway-quick-commands.sh logs-api
./railway-quick-commands.sh logs-worker
./railway-quick-commands.sh logs-beat

# 查看服務狀態
./railway-quick-commands.sh status

# 重新部署服務
./railway-quick-commands.sh deploy-worker
./railway-quick-commands.sh deploy-all

# 查看環境變數
./railway-quick-commands.sh vars-worker

# 開啟遠端 shell
./railway-quick-commands.sh shell
```

### 常用情境

**1. 修復 Worker 連接問題後重新部署**
```bash
./railway-quick-commands.sh deploy-worker
./railway-quick-commands.sh logs-worker
```

**2. 檢查所有服務狀態**
```bash
./railway-quick-commands.sh status
```

**3. 查看 Worker 環境變數確認 REDIS_URL**
```bash
./railway-quick-commands.sh vars-worker
```

---

## 📞 需要協助？

如果遇到問題，請提供：
1. 錯誤訊息截圖
2. 部署日誌（Build Logs / Deploy Logs）
3. 你正在部署哪個服務（api/worker/beat/frontend）

**快速診斷指令：**
```bash
# 查看服務狀態
./railway-quick-commands.sh status

# 查看 Worker 日誌
./railway-quick-commands.sh logs-worker

# 查看 Worker 環境變數
./railway-quick-commands.sh vars-worker
```

