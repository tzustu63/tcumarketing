# Railway 部署指南（Dockerfile 版本）

以下說明如何在 Railway 上用 **Dockerfile Builder** 部署四個服務：`tcu-api`、`tcu-worker`、`tcu-beat`、`tcu-frontend`。

## 1. 準備工作

1. **建立 Railway 專案**：於 Railway 控制台新增專案並連結到本 Git 儲存庫。
2. **建立共用資源**：在專案的 Resources 分頁新增 PostgreSQL 與 Redis，Railway 會自動注入 `DATABASE_URL` 與 `REDIS_URL`。

## 2. 為每個服務設定 Builder

在 Railway 控制台中，對四個服務依序設定：

| 服務 | Builder | Dockerfile Path |
|------|---------|-----------------|
| tcu-api | Dockerfile | `backend/Dockerfile` |
| tcu-worker | Dockerfile | `backend/Dockerfile` |
| tcu-beat | Dockerfile | `backend/Dockerfile` |
| tcu-frontend | Dockerfile | `frontend/Dockerfile` |

> ✅ 請確認 Builder 選擇 **Dockerfile**，不要使用 Railway 的 Railpack。Dockerfile 內容已依角色自動啟動對應服務。

部署前端時，可在 Build Args 填入：

```
REACT_APP_API_URL=https://<你的 API 網域或 Railway 預設 URL>
```

## 3. 設定環境變數

建議在 Environment 層級設置共用變數：

- `GOOGLE_API_KEY`
- `GOOGLE_CSE_ID`
- `LOG_LEVEL=INFO`
- `RATE_LIMIT_ENABLED=true`
- `SCRAPING_HEADLESS=true`
- `TASK_TIMEOUT=300`
- `TASK_PRIORITY_ENABLED=true`

各服務再補上個別變數：

- `tcu-api`：`SERVICE_ROLE=api`、`API_HOST=0.0.0.0`、`API_PORT=8000`
- `tcu-worker`：`SERVICE_ROLE=worker`、`TASK_MAX_WORKERS=4`
- `tcu-beat`：`SERVICE_ROLE=beat`
- `tcu-frontend`：`NODE_ENV=production`、`REACT_APP_API_URL`（若未在 Build Args 指定，可改放在環境變數）

Railway 會自動帶入 `DATABASE_URL` 與 `REDIS_URL`，Celery 亦會使用同一組連線。

## 4. 部署流程

1. 推送程式碼到 Git 遠端，確保 Dockerfile 已更新。
2. 在 Railway 控制台為每個服務點擊 **Deploy** 或啟用自動部署。
3. 等待 Build 完成後，於 Logs 分頁確認容器啟動狀態。

### 初次部署需執行的動作

- **資料庫遷移**（於 `tcu-api` 服務執行）：
  ```bash
  railway run --service tcu-api alembic upgrade head
  ```
- （選用）檢查 Worker / Beat 日誌，確認已連上 Redis 與資料庫。

## 5. 驗證檢查

1. 開啟 `tcu-api` 服務的預設網域 `https://<服務名稱>.up.railway.app/docs` 確認 API 正常。
2. 造訪 `tcu-frontend` 的預設網域並測試匯出功能。
3. 若需自訂網域，至 Railway 的 Domains 分頁綁定 DNS。

## 6. 管理與疑難排解

- 查看日誌：在服務的 Logs 分頁觀察錯誤訊息。
- 重新部署：調整環境變數或 Build Args 後，點擊 **Redeploy**。
- 若 Build 失敗，請在本機執行 `docker build` 驗證 Dockerfile。
- 需要 Shell 除錯時，可使用 Railway CLI：
  ```bash
  npm install -g @railway/cli
  railway login
  railway shell --service tcu-api
  ```

依照以上流程即可在 Railway 上使用 Dockerfile 完成部署，過程中完全不需要 Railpack。

