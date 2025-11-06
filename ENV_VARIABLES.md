# 環境變數說明文件 (Environment Variables Documentation)

本文件詳細說明慈濟大學招生通路自動開發系統的所有環境變數配置。

## 目錄

- [資料庫配置](#資料庫配置)
- [Redis 配置](#redis-配置)
- [Celery 配置](#celery-配置)
- [API 配置](#api-配置)
- [CORS 配置](#cors-配置)
- [爬蟲配置](#爬蟲配置)
- [速率限制配置](#速率限制配置)
- [任務配置](#任務配置)
- [匯出配置](#匯出配置)
- [日誌配置](#日誌配置)
- [前端配置](#前端配置)
- [安全配置](#安全配置)
- [監控配置](#監控配置)
- [進階配置](#進階配置)

## 資料庫配置

### DATABASE_URL

- **類型**: String
- **必填**: 是
- **預設值**: `postgresql://user:password@localhost:5432/recruitment`
- **說明**: PostgreSQL 資料庫完整連線 URL
- **格式**: `postgresql://[使用者]:[密碼]@[主機]:[埠號]/[資料庫名稱]`
- **範例**:
  ```bash
  # 本地開發
  DATABASE_URL=postgresql://user:password@localhost:5432/recruitment
  
  # Docker 環境
  DATABASE_URL=postgresql://user:password@db:5432/recruitment
  
  # 遠端資料庫
  DATABASE_URL=postgresql://admin:SecurePass123@db.example.com:5432/recruitment
  ```

### DB_HOST

- **類型**: String
- **必填**: 否
- **預設值**: `localhost`
- **說明**: 資料庫主機位址
- **範例**: `localhost`, `db`, `192.168.1.100`, `db.example.com`

### DB_PORT

- **類型**: Integer
- **必填**: 否
- **預設值**: `5432`
- **說明**: 資料庫連接埠
- **範例**: `5432`, `5433`

### DB_NAME

- **類型**: String
- **必填**: 否
- **預設值**: `recruitment`
- **說明**: 資料庫名稱
- **範例**: `recruitment`, `recruitment_prod`, `recruitment_dev`

### DB_USER

- **類型**: String
- **必填**: 否
- **預設值**: `user`
- **說明**: 資料庫使用者名稱
- **範例**: `user`, `admin`, `recruitment_user`

### DB_PASSWORD

- **類型**: String
- **必填**: 否
- **預設值**: `password`
- **說明**: 資料庫密碼
- **安全建議**: 
  - 開發環境可使用簡單密碼
  - 生產環境必須使用強密碼（至少 16 字元，包含大小寫字母、數字、特殊符號）
- **範例**: 
  ```bash
  # 開發環境
  DB_PASSWORD=password
  
  # 生產環境
  DB_PASSWORD=Xk9#mP2$vL8@qR5!nT7&wY3
  ```

## Redis 配置

### REDIS_URL

- **類型**: String
- **必填**: 是
- **預設值**: `redis://localhost:6379/0`
- **說明**: Redis 連線 URL
- **格式**: `redis://[主機]:[埠號]/[資料庫編號]`
- **範例**:
  ```bash
  # 本地開發
  REDIS_URL=redis://localhost:6379/0
  
  # Docker 環境
  REDIS_URL=redis://redis:6379/0
  
  # 有密碼的 Redis
  REDIS_URL=redis://:password@redis:6379/0
  ```

### REDIS_HOST

- **類型**: String
- **必填**: 否
- **預設值**: `localhost`
- **說明**: Redis 主機位址

### REDIS_PORT

- **類型**: Integer
- **必填**: 否
- **預設值**: `6379`
- **說明**: Redis 連接埠

## Celery 配置

### CELERY_BROKER_URL

- **類型**: String
- **必填**: 是
- **預設值**: `redis://localhost:6379/0`
- **說明**: Celery 訊息佇列 Broker URL
- **建議**: 使用與 REDIS_URL 相同的值

### CELERY_RESULT_BACKEND

- **類型**: String
- **必填**: 是
- **預設值**: `redis://localhost:6379/0`
- **說明**: Celery 任務結果儲存後端
- **建議**: 使用與 REDIS_URL 相同的值

## API 配置

### API_HOST

- **類型**: String
- **必填**: 否
- **預設值**: `0.0.0.0`
- **說明**: API 服務監聽的主機位址
- **選項**:
  - `0.0.0.0` - 監聽所有網路介面
  - `127.0.0.1` - 僅監聽本地
  - 特定 IP 位址

### API_PORT

- **類型**: Integer
- **必填**: 否
- **預設值**: `8000`
- **說明**: API 服務監聽的連接埠
- **範例**: `8000`, `8080`, `3001`

### API_RELOAD

- **類型**: Boolean
- **必填**: 否
- **預設值**: `true`
- **說明**: 開發模式自動重載
- **選項**:
  - `true` - 程式碼變更時自動重載（開發環境）
  - `false` - 不自動重載（生產環境）

## CORS 配置

### CORS_ORIGINS

- **類型**: String (逗號分隔)
- **必填**: 否
- **預設值**: `http://localhost:3000,http://localhost:8000`
- **說明**: 允許的跨域來源網址
- **格式**: 多個網址用逗號分隔，不含空格
- **範例**:
  ```bash
  # 開發環境
  CORS_ORIGINS=http://localhost:3000,http://localhost:8000
  
  # 生產環境
  CORS_ORIGINS=https://app.example.com,https://api.example.com
  
  # 多個域名
  CORS_ORIGINS=https://app.example.com,https://admin.example.com,https://api.example.com
  ```

## 爬蟲配置

### SCRAPING_HEADLESS

- **類型**: Boolean
- **必填**: 否
- **預設值**: `true`
- **說明**: 瀏覽器無頭模式
- **選項**:
  - `true` - 不顯示瀏覽器視窗（建議）
  - `false` - 顯示瀏覽器視窗（除錯用）

### SCRAPING_USER_AGENTS

- **類型**: String (逗號分隔)
- **必填**: 否
- **預設值**: `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36,Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36`
- **說明**: User-Agent 列表，系統會隨機輪換使用
- **建議**: 使用多個常見的 User-Agent 字串
- **範例**:
  ```bash
  SCRAPING_USER_AGENTS=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36,Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36,Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36
  ```

### SCRAPING_MIN_DELAY

- **類型**: Integer
- **必填**: 否
- **預設值**: `2`
- **說明**: 請求之間的最小延遲時間（秒）
- **範圍**: 1-10
- **建議**: 2-3 秒

### SCRAPING_MAX_DELAY

- **類型**: Integer
- **必填**: 否
- **預設值**: `5`
- **說明**: 請求之間的最大延遲時間（秒）
- **範圍**: 3-15
- **建議**: 5-8 秒
- **注意**: 必須大於 SCRAPING_MIN_DELAY

### SCRAPING_MAX_RETRIES

- **類型**: Integer
- **必填**: 否
- **預設值**: `3`
- **說明**: 請求失敗時的最大重試次數
- **範圍**: 1-5
- **建議**: 3 次

### SCRAPING_TIMEOUT

- **類型**: Integer
- **必填**: 否
- **預設值**: `30`
- **說明**: 請求超時時間（秒）
- **範圍**: 10-60
- **建議**: 30 秒

## 速率限制配置

### RATE_LIMIT_ENABLED

- **類型**: Boolean
- **必填**: 否
- **預設值**: `true`
- **說明**: 是否啟用速率限制
- **建議**: 生產環境必須啟用

### RATE_LIMIT_MAX_REQUESTS_PER_DOMAIN

- **類型**: Integer
- **必填**: 否
- **預設值**: `10`
- **說明**: 每個域名在時間窗口內的最大請求數
- **範圍**: 5-50
- **建議**: 10-20

### RATE_LIMIT_DOMAIN_TIME_WINDOW

- **類型**: Integer
- **必填**: 否
- **預設值**: `60`
- **說明**: 域名請求限制的時間窗口（秒）
- **範圍**: 30-300
- **建議**: 60 秒

### RATE_LIMIT_MIN_REQUEST_INTERVAL

- **類型**: Float
- **必填**: 否
- **預設值**: `2.0`
- **說明**: 請求之間的最小間隔時間（秒）
- **範圍**: 1.0-10.0
- **建議**: 2.0-3.0

### RATE_LIMIT_MAX_REQUESTS_PER_MINUTE

- **類型**: Integer
- **必填**: 否
- **預設值**: `60`
- **說明**: 全域每分鐘最大請求數
- **範圍**: 30-300
- **建議**: 60-120

### RATE_LIMIT_MAX_CONCURRENT_REQUESTS

- **類型**: Integer
- **必填**: 否
- **預設值**: `10`
- **說明**: 最大並行請求數
- **範圍**: 5-50
- **建議**: 10-20

## 任務配置

### TASK_TIMEOUT

- **類型**: Integer
- **必填**: 否
- **預設值**: `300`
- **說明**: 任務執行超時時間（秒）
- **範圍**: 60-3600
- **建議**: 300-600

### TASK_MAX_WORKERS

- **類型**: Integer
- **必填**: 否
- **預設值**: `4`
- **說明**: Celery Worker 並行處理數
- **範圍**: 1-16
- **建議**: 
  - 開發環境: 2-4
  - 生產環境: 4-8
- **注意**: 根據 CPU 核心數調整

### TASK_PRIORITY_ENABLED

- **類型**: Boolean
- **必填**: 否
- **預設值**: `true`
- **說明**: 是否啟用任務優先級管理

### TASK_MAX_TASKS_PER_CHILD

- **類型**: Integer
- **必填**: 否
- **預設值**: `1000`
- **說明**: 每個 Worker 處理多少任務後重啟
- **範圍**: 100-10000
- **建議**: 1000
- **用途**: 防止記憶體洩漏

## 匯出配置

### EXPORT_DIR

- **類型**: String
- **必填**: 否
- **預設值**: `./exports`
- **說明**: 匯出檔案儲存目錄
- **範例**: `./exports`, `/data/exports`, `/mnt/storage/exports`

### EXPORT_MAX_RECORDS

- **類型**: Integer
- **必填**: 否
- **預設值**: `10000`
- **說明**: 單次匯出最大記錄數
- **範圍**: 1000-100000
- **建議**: 10000-50000

### EXPORT_FILE_RETENTION_DAYS

- **類型**: Integer
- **必填**: 否
- **預設值**: `30`
- **說明**: 匯出檔案保留天數
- **範圍**: 7-365
- **建議**: 30-90

## 日誌配置

### LOG_LEVEL

- **類型**: String
- **必填**: 否
- **預設值**: `INFO`
- **說明**: 日誌等級
- **選項**:
  - `DEBUG` - 除錯資訊（最詳細）
  - `INFO` - 一般資訊
  - `WARNING` - 警告訊息
  - `ERROR` - 錯誤訊息
  - `CRITICAL` - 嚴重錯誤（最少）
- **建議**:
  - 開發環境: `DEBUG` 或 `INFO`
  - 生產環境: `WARNING` 或 `ERROR`

### LOG_FILE

- **類型**: String
- **必填**: 否
- **預設值**: `./logs/app.log`
- **說明**: 日誌檔案路徑
- **範例**: `./logs/app.log`, `/var/log/recruitment/app.log`

### LOG_MAX_SIZE

- **類型**: Integer
- **必填**: 否
- **預設值**: `100`
- **說明**: 單個日誌檔案最大大小（MB）
- **範圍**: 10-1000
- **建議**: 100-500

### LOG_BACKUP_COUNT

- **類型**: Integer
- **必填**: 否
- **預設值**: `10`
- **說明**: 保留的日誌檔案數量
- **範圍**: 5-100
- **建議**: 10-30

## 前端配置

### FRONTEND_PORT

- **類型**: Integer
- **必填**: 否
- **預設值**: `3000`
- **說明**: 前端服務連接埠
- **範例**: `3000`, `3001`, `8080`

### REACT_APP_API_URL

- **類型**: String
- **必填**: 是
- **預設值**: `http://localhost:8000`
- **說明**: 前端連接的 API 基礎 URL
- **範例**:
  ```bash
  # 開發環境
  REACT_APP_API_URL=http://localhost:8000
  
  # 生產環境
  REACT_APP_API_URL=https://api.example.com
  ```

### NODE_ENV

- **類型**: String
- **必填**: 否
- **預設值**: `development`
- **說明**: Node.js 環境
- **選項**:
  - `development` - 開發環境
  - `production` - 生產環境

## 安全配置

### SECRET_KEY

- **類型**: String
- **必填**: 否（未來版本可能需要）
- **預設值**: 無
- **說明**: JWT 加密密鑰
- **建議**: 使用隨機生成的強密鑰
- **生成方法**:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```

### JWT_EXPIRATION_MINUTES

- **類型**: Integer
- **必填**: 否
- **預設值**: `60`
- **說明**: JWT Token 過期時間（分鐘）
- **範圍**: 15-1440
- **建議**: 60-120

## 監控配置

### ALERT_ERROR_RATE_THRESHOLD

- **類型**: Integer
- **必填**: 否
- **預設值**: `20`
- **說明**: 錯誤率告警閾值（百分比）
- **範圍**: 5-50
- **建議**: 20-30

### ALERT_TASK_DURATION_THRESHOLD

- **類型**: Integer
- **必填**: 否
- **預設值**: `1800`
- **說明**: 任務執行時間告警閾值（秒）
- **範圍**: 300-7200
- **建議**: 1800-3600

## 進階配置

### DB_POOL_SIZE

- **類型**: Integer
- **必填**: 否
- **預設值**: `20`
- **說明**: 資料庫連線池大小
- **範圍**: 5-100
- **建議**: 20-50

### DB_MAX_OVERFLOW

- **類型**: Integer
- **必填**: 否
- **預設值**: `10`
- **說明**: 資料庫連線池最大溢出數
- **範圍**: 5-50
- **建議**: 10-20

### REDIS_POOL_SIZE

- **類型**: Integer
- **必填**: 否
- **預設值**: `50`
- **說明**: Redis 連線池大小
- **範圍**: 10-200
- **建議**: 50-100

### DEBUG

- **類型**: Boolean
- **必填**: 否
- **預設值**: `false`
- **說明**: 除錯模式
- **選項**:
  - `true` - 啟用除錯模式（開發環境）
  - `false` - 關閉除錯模式（生產環境）
- **警告**: 生產環境必須設為 `false`

## 環境配置範例

### 開發環境 (.env.development)

```bash
# 資料庫
DATABASE_URL=postgresql://user:password@localhost:5432/recruitment
DB_USER=user
DB_PASSWORD=password

# Redis
REDIS_URL=redis://localhost:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# 日誌
LOG_LEVEL=DEBUG
DEBUG=true

# 任務
TASK_MAX_WORKERS=2

# 前端
REACT_APP_API_URL=http://localhost:8000
NODE_ENV=development
```

### 生產環境 (.env.production)

```bash
# 資料庫
DATABASE_URL=postgresql://admin:StrongPassword123!@db:5432/recruitment
DB_USER=admin
DB_PASSWORD=StrongPassword123!

# Redis
REDIS_URL=redis://:RedisPass456@redis:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false

# CORS
CORS_ORIGINS=https://app.example.com,https://api.example.com

# 日誌
LOG_LEVEL=WARNING
DEBUG=false

# 任務
TASK_MAX_WORKERS=8
TASK_TIMEOUT=600

# 速率限制
RATE_LIMIT_ENABLED=true
RATE_LIMIT_MAX_REQUESTS_PER_DOMAIN=15
RATE_LIMIT_MIN_REQUEST_INTERVAL=3.0

# 前端
REACT_APP_API_URL=https://api.example.com
NODE_ENV=production
```

## 配置檢查清單

部署前請確認以下配置：

### 開發環境
- [ ] 資料庫連線正確
- [ ] Redis 連線正確
- [ ] API 可以訪問
- [ ] 前端可以連接 API
- [ ] 日誌等級設為 DEBUG 或 INFO

### 生產環境
- [ ] 使用強密碼
- [ ] API_RELOAD 設為 false
- [ ] DEBUG 設為 false
- [ ] LOG_LEVEL 設為 WARNING 或 ERROR
- [ ] CORS_ORIGINS 設定正確的域名
- [ ] 啟用速率限制
- [ ] 配置適當的 Worker 數量
- [ ] 設定備份策略
- [ ] 配置監控告警

## 故障排除

### 配置錯誤

**症狀**: 服務無法啟動

**檢查**:
```bash
# 檢查環境變數是否載入
docker-compose config

# 檢查特定服務的環境變數
docker-compose exec api env | grep DATABASE_URL
```

### 連線問題

**症狀**: 無法連接資料庫或 Redis

**檢查**:
```bash
# 測試資料庫連線
docker-compose exec api python -c "from app.database import engine; engine.connect()"

# 測試 Redis 連線
docker-compose exec api python -c "from redis import Redis; r = Redis.from_url('redis://redis:6379/0'); print(r.ping())"
```

## 安全建議

1. **不要在版本控制中提交 .env 檔案**
   ```bash
   # 確保 .env 在 .gitignore 中
   echo ".env" >> .gitignore
   ```

2. **使用環境變數管理工具**
   - Docker Secrets
   - Kubernetes Secrets
   - AWS Secrets Manager
   - HashiCorp Vault

3. **定期輪換密碼**
   - 資料庫密碼每 90 天更換
   - API 密鑰每 180 天更換

4. **最小權限原則**
   - 資料庫使用者僅授予必要權限
   - 不使用 root 或 admin 帳號

---

**版本**: 1.0  
**最後更新**: 2024-01-03
