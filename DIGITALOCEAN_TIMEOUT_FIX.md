# Digital Ocean 部署 - Timeout 問題修正指南

## 問題總結

在 Digital Ocean 部署時遇到以下問題：

### 1. 前端 Timeout 錯誤
```
AxiosError: timeout of 10000ms exceeded
```
- **位置**: TaskForm.js:278 → taskService.createTask
- **原因**: 創建任務時前端請求超時

### 2. 後端 Celery 連接問題
- 創建任務時，後端嘗試啟動 Celery 任務
- 如果 Redis/Celery 未正常運行，會導致 API 請求掛起直到超時
- 容器間網絡通訊可能存在問題

## 已實施的修正

### ✅ 修正 1：前端 API 超時和錯誤處理

**檔案**: `frontend/src/services/api.js`

**變更內容**:
- 將 timeout 從 30秒 增加到 **60秒**
- 添加 API Base URL 的 console 日誌，便於調試
- 改進錯誤訊息處理

**程式碼**:
```javascript
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 秒超時（針對任務創建等耗時操作）
  headers: {
    "Content-Type": "application/json",
  },
});

console.log('API Base URL:', API_BASE_URL);
```

### ✅ 修正 2：後端 Celery 連接處理優化

**檔案**: `backend/app/api/routes/tasks.py`

**變更內容**:
- 使用 `apply_async` 替代 `delay`，設置任務過期時間
- **不再拋出異常**當 Celery 連接失敗時
- 任務仍然會被創建，但狀態標記為 `failed`
- 前端可以看到任務創建成功但啟動失敗的詳細訊息

**程式碼**:
```python
try:
    scrape_google_task.apply_async(
        args=[str(created_task.id)],
        expires=300  # 任務在 5 分鐘內必須被執行
    )
except Exception as e:
    logger.error(f"Failed to queue task {created_task.id}: {str(e)}")
    
    task_repo.update(str(created_task.id), {
        "status": "failed",
        "error_message": f"Failed to queue task: {str(e)}. Please check if Celery workers are running."
    })
    
    # 不拋出異常，返回狀態為 failed 的任務
    created_task.status = "failed"
    created_task.error_message = f"Failed to queue task..."
```

### ✅ 修正 3：增強健康檢查端點

**檔案**: `backend/app/main.py`

**變更內容**:
- 添加資料庫連接檢查
- 添加 Celery/Redis 連接檢查
- 返回詳細的健康狀態資訊

**測試**:
```bash
curl http://YOUR_DROPLET_IP:8000/health
```

**回應範例**:
```json
{
  "status": "healthy",
  "api": "ok",
  "database": "ok",
  "celery": "ok",
  "timestamp": "2025-11-06T23:45:00.123456"
}
```

如果有問題：
```json
{
  "status": "degraded",
  "api": "ok",
  "database": "ok",
  "celery": "no_workers",
  "timestamp": "2025-11-06T23:45:00.123456"
}
```

### ✅ 修正 4：Docker Compose 生產環境配置

**檔案**: `docker-compose.prod.yml`

**變更內容**:
- 優化前端構建參數
- 添加 `depends_on: - api` 確保啟動順序
- 移除不必要的環境變數重複

### ✅ 修正 5：部署腳本 CORS 配置

**檔案**: `deploy-to-digitalocean.sh`

**變更內容**:
- 修正 CORS_ORIGINS 格式（逗號分隔，不使用 JSON 陣列）
- 添加 API 自身的 URL 到 CORS 允許列表

**正確格式**:
```bash
CORS_ORIGINS=http://${DROPLET_IP}:3000,http://localhost:3000,http://${DROPLET_IP}:8000
```

## 部署步驟（Digital Ocean）

### 1. 確保環境變數正確設定

在 `/opt/apps/.env` 中：

```bash
# 資料庫配置
DB_USER=recruitment_user
DB_PASSWORD=your_secure_password
DB_NAME=recruitment_db

# Redis 配置
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# API 配置
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://YOUR_DROPLET_IP:3000,http://localhost:3000

# 前端配置（重要！）
REACT_APP_API_URL=http://YOUR_DROPLET_IP:8000

# Celery 配置
TASK_MAX_WORKERS=4
TASK_TIMEOUT=600

# 其他配置
LOG_LEVEL=INFO
SCRAPING_HEADLESS=true
RATE_LIMIT_ENABLED=true
```

### 2. 重新構建並啟動服務

```bash
cd /opt/apps

# 停止服務
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# 重新構建
docker compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache

# 啟動服務
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 等待服務啟動
sleep 30
```

### 3. 檢查服務狀態

```bash
# 查看所有容器狀態
docker compose ps

# 應該看到：
# recruitment-api        Up      0.0.0.0:8000->8000/tcp
# recruitment-worker     Up
# recruitment-beat       Up
# recruitment-frontend   Up      0.0.0.0:3000->3000/tcp
# recruitment-db         Up (healthy)
# recruitment-redis      Up (healthy)
```

### 4. 測試健康檢查

```bash
# 測試 API 健康狀態
curl http://localhost:8000/health

# 從外部測試（替換為你的 IP）
curl http://YOUR_DROPLET_IP:8000/health
```

### 5. 檢查容器日誌

```bash
# API 日誌
docker compose logs api -f --tail 50

# Worker 日誌（檢查 Celery 是否正常）
docker compose logs worker -f --tail 50

# Frontend 日誌
docker compose logs frontend -f --tail 20
```

### 6. 測試前端連接

在瀏覽器中打開：
```
http://YOUR_DROPLET_IP:3000
```

打開瀏覽器開發者工具（F12），查看 Console：
- 應該看到 `API Base URL: http://YOUR_DROPLET_IP:8000`
- 嘗試創建任務，觀察網絡請求

## 故障排除

### 問題 1：前端仍然顯示 timeout

**檢查步驟**:
```bash
# 1. 檢查 API 是否可訪問
curl http://localhost:8000/health

# 2. 檢查前端環境變數
docker compose exec frontend env | grep REACT_APP

# 3. 查看前端構建日誌
docker compose logs frontend | grep "API"
```

**解決方案**:
```bash
# 重新構建前端，確保環境變數正確
docker compose -f docker-compose.yml -f docker-compose.prod.yml build frontend --no-cache
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d frontend
```

### 問題 2：Celery workers 未運行

**檢查**:
```bash
# 檢查 worker 狀態
docker compose logs worker --tail 50

# 檢查 Redis 連接
docker compose exec worker python -c "
from app.celery_app import celery_app
print(celery_app.control.inspect().active())
"
```

**常見錯誤**:
- `ConnectionRefusedError`: Redis 未啟動或連接配置錯誤
- `ModuleNotFoundError`: 缺少依賴（應該已修正）

**解決方案**:
```bash
# 重啟 Redis 和 Worker
docker compose restart redis
sleep 5
docker compose restart worker beat
```

### 問題 3：創建任務失敗但沒有錯誤訊息

**檢查**:
```bash
# 查看 API 日誌
docker compose logs api | grep "Failed to queue"

# 查看資料庫中的任務
docker compose exec db psql -U recruitment_user -d recruitment_db -c \
  "SELECT id, status, error_message, created_at FROM tasks ORDER BY created_at DESC LIMIT 5;"
```

### 問題 4：CORS 錯誤

**錯誤訊息**:
```
Access to XMLHttpRequest at 'http://...' from origin 'http://...' 
has been blocked by CORS policy
```

**解決方案**:
```bash
# 1. 檢查當前 CORS 設定
docker compose exec api env | grep CORS_ORIGINS

# 2. 更新 .env 文件
nano /opt/apps/.env
# 確保包含：
CORS_ORIGINS=http://YOUR_IP:3000,http://localhost:3000,http://YOUR_IP:8000

# 3. 重啟 API
docker compose restart api
```

## 監控和維護

### 持續監控腳本

創建 `/opt/scripts/monitor.sh`:

```bash
#!/bin/bash

echo "=== Health Check ==="
curl -s http://localhost:8000/health | jq .

echo ""
echo "=== Container Status ==="
cd /opt/apps
docker compose ps

echo ""
echo "=== Recent Errors ==="
docker compose logs --tail 20 --since 1h 2>&1 | grep -i error | tail -10
```

設置 Cron 定期檢查：
```bash
# 每 5 分鐘檢查一次
*/5 * * * * /opt/scripts/monitor.sh >> /var/log/recruitment-monitor.log 2>&1
```

### 效能優化建議

1. **調整 Worker 數量**（根據 CPU 核心）:
   ```bash
   # 2 核心 → 4 workers
   # 4 核心 → 8 workers
   TASK_MAX_WORKERS=4
   ```

2. **增加任務超時時間**（如果處理大量數據）:
   ```bash
   TASK_TIMEOUT=600  # 10 分鐘
   ```

3. **啟用 Redis 持久化**:
   ```yaml
   redis:
     command: redis-server --appendonly yes --maxmemory 256mb
   ```

## 成功指標

✅ 健康檢查返回 `status: "healthy"`
✅ 所有容器狀態為 `Up` 或 `Up (healthy)`
✅ 前端可以加載並顯示 API Base URL
✅ 可以成功創建任務（即使 worker 不可用也會有明確的錯誤訊息）
✅ Worker 日誌顯示正在處理任務

## 總結

此次修正主要解決了：

1. **前端超時問題** - 增加超時時間並改進錯誤處理
2. **後端 Celery 連接** - 優雅處理連接失敗，不阻塞 API 響應
3. **健康檢查** - 提供詳細的系統狀態資訊
4. **配置優化** - 修正 CORS、環境變數等配置問題

現在系統更加健壯，即使 Celery workers 暫時不可用，前端仍然可以創建任務並獲得明確的錯誤訊息。

## 聯繫支援

如果問題仍然存在，請收集以下資訊：

```bash
# 生成診斷報告
cat > /tmp/diagnostic.txt << EOF
=== System Info ===
$(uname -a)
$(docker --version)
$(docker compose version)

=== Container Status ===
$(docker compose ps)

=== Health Check ===
$(curl -s http://localhost:8000/health)

=== Environment ===
$(cat .env | grep -v PASSWORD | grep -v SECRET)

=== Recent Logs ===
$(docker compose logs --tail 100)
EOF

cat /tmp/diagnostic.txt
```

---

**版本**: 1.0
**更新日期**: 2025-11-06
**適用於**: Digital Ocean 部署



