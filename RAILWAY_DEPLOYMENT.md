# Railway 部署指南

本文件協助你以 Railway 部署慈濟大學招生通路自動開發系統。流程包含建立多個服務（API、Celery Worker、Celery Beat、Frontend），以及使用 Railway 的 PostgreSQL、Redis 資源。

## 1. 前置準備

- 安裝 Railway CLI：
  ```bash
  npm install -g @railway/cli
  ```
- 登入帳號：
  ```bash
  railway login
  ```
- 建議先在 Railway 控制台建立專案，或直接於 CLI 執行 `railway init` 讓腳本自動建立。

## 2. 調整程式架構重點

- `backend/start.sh` 根據 `SERVICE_ROLE` 啟動對應進程：
  - `api`：啟動 FastAPI (`uvicorn`)，可用 `UVICORN_RELOAD=true` 控制是否自動重載。
  - `worker`：啟動 Celery Worker，尊重 `TASK_MAX_WORKERS`、`LOG_LEVEL` 等變數。
  - `beat`：啟動 Celery Beat。
- `backend/Dockerfile` 改為執行 `start.sh`，並支援 `PORT` 環境變數（Railway 預設會注入）。
- `frontend` 改以 `start.sh` 動態生成 Nginx 設定，確保符合 Railway 指派的 `PORT`。
- `docker-compose.yml`/`docker-compose.prod.yml` 同步設定 `SERVICE_ROLE`，確保本地與 Railway 一致。
- Celery 參數會自動 fallback 至 `REDIS_URL`，因此不需額外設定 `CELERY_BROKER_URL`、`CELERY_RESULT_BACKEND`。

## 3. 使用 `deploy-to-railway.sh`

腳本主要協助確認 CLI 是否可用、專案與環境是否綁定成功，並在檢查資源後列出後續「手動步驟清單」。新版 Railway CLI 不再提供在指令裡直接建立服務、設定環境變數或新增資源，因此腳本不會自動部署程式碼。建議流程如下：

```bash
cd /Users/kuoyuming/Desktop/程式開發/auto scraper for oga
bash deploy-to-railway.sh
```

腳本完成後，依照終端上顯示的指引或下列步驟手動處理：

1. **建立服務與部署程式碼**
   - 建議在 Railway 控制台依序建立 `tcu-api`、`tcu-worker`、`tcu-beat`、`tcu-frontend`。
   - 若偏好 CLI，可切換到 `backend/`、`frontend/` 目錄執行 `railway up`，部署完成後於控制台重新命名服務。

2. **設定環境變數**
   - 對每個服務執行 `railway variables --service <服務名稱> --environment production`，互動式輸入：
     - `GOOGLE_API_KEY`
     - `GOOGLE_CSE_ID`
     - `SERVICE_ROLE`（api / worker / beat）
     - 其他必要的設定，例如 `PORT`、`UVICORN_RELOAD`、`REACT_APP_API_URL` 等。

3. **建立 PostgreSQL 與 Redis**
   - 目前 CLI 無法在腳本內建立資源，請到 Railway 控制台 → Resources 新增 PostgreSQL 與 Redis，並連結到專案。
   - 服務中即可使用 Railway 自動注入的 `DATABASE_URL`、`REDIS_URL`。

4. **執行資料庫遷移**
   ```bash
   railway run --service tcu-api alembic upgrade head
   ```

5. **驗證與後續調整**
   - 檢查各服務的 Deployments、Logs。
   - 造訪前端與 API URL，確認是否正常。
   - 依需求微調環境變數或自訂網域。

## 4. 環境變數參考

共用（設於 Environment 層級）：
- `GOOGLE_API_KEY`
- `GOOGLE_CSE_ID`
- `API_HOST=0.0.0.0`
- `API_PORT=8000`
- `LOG_LEVEL=INFO`
- `RATE_LIMIT_ENABLED=true`
- `SCRAPING_HEADLESS=true`
- `TASK_TIMEOUT=300`
- `TASK_PRIORITY_ENABLED=true`

服務層級：
- API：`SERVICE_ROLE=api`、`PORT=8000`、`UVICORN_RELOAD=false`
- Worker：`SERVICE_ROLE=worker`、`TASK_MAX_WORKERS=8`
- Beat：`SERVICE_ROLE=beat`
- Frontend：`NODE_ENV=production`、`REACT_APP_API_URL=<API URL>`

Railway 的 PostgreSQL/Redis 資源會自動注入 `DATABASE_URL`、`REDIS_URL` 等連線字串，不需額外設定。

## 5. 部署後檢查

- 於 Railway 控制台查看各服務的 Deployments 與 Logs，確保啟動成功。
- 前端預設 URL：`https://tcu-frontend.up.railway.app`（Railway 會依專案命名），可綁定自訂網域。
- API Swagger：`https://tcu-api.up.railway.app/docs`
- 若需調整環境變數，修改後可在 UI 直接重新部署服務。
- 初次部署後執行資料庫遷移：
  ```bash
  railway run --service tcu-api alembic upgrade head
  ```

## 6. 已知限制

- Celery 任務與爬蟲長時間執行時，請留意 Railway 計費方案的資源限制與自動休眠機制。
- 匯出檔案應改存外部儲存服務，避免部署重啟時遺失。
- 如需橫向擴充（多個 Worker/Beat），可複製服務並調整 `TASK_MAX_WORKERS` 或使用 Railway 的垂直擴充方案。
- Railway 自動注入的 `REDIS_URL`、`DATABASE_URL` 會被所有服務共用，Celery 自動 fallback，毋須額外設定。

如部署過程遇到指令相容性問題，可使用 `railway --help` 查看最新 CLI 語法，或於 Railway 控制台手動完成相同設定。

