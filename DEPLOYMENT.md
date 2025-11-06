# 部署指南 (Deployment Guide)

慈濟大學招生通路自動開發系統部署文件

## 目錄

- [系統需求](#系統需求)
- [開發環境部署](#開發環境部署)
- [生產環境部署](#生產環境部署)
- [資料庫遷移](#資料庫遷移)
- [監控與維護](#監控與維護)
- [故障排除](#故障排除)
- [備份與恢復](#備份與恢復)

## 系統需求

### 硬體需求

**最低配置**
- CPU: 2 核心
- RAM: 4 GB
- 硬碟: 20 GB SSD

**建議配置**
- CPU: 4 核心以上
- RAM: 8 GB 以上
- 硬碟: 50 GB SSD

### 軟體需求

- Docker 20.10+
- Docker Compose 2.0+
- Git 2.30+

**本地開發額外需求**
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (可選)
- Redis 7+ (可選)

## 開發環境部署

### 1. 克隆專案

```bash
git clone <repository-url>
cd indonesia-recruitment-automation
```

### 2. 配置環境變數

```bash
# 複製環境變數範本
cp .env.example .env

# 編輯 .env 檔案，根據需要調整配置
nano .env
```

### 3. 啟動服務

```bash
# 啟動所有服務
docker-compose up -d

# 查看服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f
```

### 4. 初始化資料庫

```bash
# 進入 API 容器
docker-compose exec api bash

# 執行資料庫遷移
alembic upgrade head

# (可選) 載入種子資料
python scripts/seed_data.py

# 退出容器
exit
```

### 5. 驗證部署

訪問以下 URL 確認服務正常運行：

- 前端: http://localhost:3000
- API 文件: http://localhost:8000/docs
- API 健康檢查: http://localhost:8000/health

### 6. 停止服務

```bash
# 停止所有服務
docker-compose down

# 停止並刪除所有資料（包含資料庫）
docker-compose down -v
```

## 生產環境部署

### 1. 準備生產環境配置

```bash
# 複製環境變數範本
cp .env.example .env.production

# 編輯生產環境配置
nano .env.production
```

**重要配置項目**：

```bash
# 使用強密碼
DB_PASSWORD=<strong-random-password>

# 關閉除錯模式
DEBUG=false
API_RELOAD=false

# 調整日誌等級
LOG_LEVEL=WARNING

# 設定正確的 CORS 來源
CORS_ORIGINS=https://yourdomain.com

# 增加 Worker 數量
TASK_MAX_WORKERS=8
```

### 2. 建立生產環境映像

```bash
# 建立 Docker 映像
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# 推送到映像倉庫（如果使用）
docker-compose push
```

### 3. 啟動生產環境

```bash
# 使用生產配置啟動
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 查看服務狀態
docker-compose ps
```

### 4. 配置 Nginx 反向代理（可選）

建立 `nginx/nginx.conf`：

```nginx
events {
    worker_connections 1024;
}

http {
    upstream api_backend {
        server api:8000;
    }

    upstream frontend_backend {
        server frontend:3000;
    }

    server {
        listen 80;
        server_name yourdomain.com;

        # 前端
        location / {
            proxy_pass http://frontend_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # API
        location /api {
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # API 文件
        location /docs {
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
        }
    }
}
```

### 5. 配置 SSL/TLS（建議）

使用 Let's Encrypt 獲取免費 SSL 憑證：

```bash
# 安裝 certbot
sudo apt-get install certbot python3-certbot-nginx

# 獲取憑證
sudo certbot --nginx -d yourdomain.com

# 自動更新憑證
sudo certbot renew --dry-run
```

### 6. 設定系統服務（可選）

建立 systemd 服務檔案 `/etc/systemd/system/recruitment.service`：

```ini
[Unit]
Description=Indonesia Recruitment Automation System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/indonesia-recruitment-automation
ExecStart=/usr/local/bin/docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

啟用服務：

```bash
sudo systemctl enable recruitment
sudo systemctl start recruitment
sudo systemctl status recruitment
```

## 資料庫遷移

### 建立新的遷移

```bash
# 進入 API 容器
docker-compose exec api bash

# 自動生成遷移腳本
alembic revision --autogenerate -m "描述變更內容"

# 檢查生成的遷移腳本
cat alembic/versions/<timestamp>_描述變更內容.py

# 執行遷移
alembic upgrade head
```

### 回滾遷移

```bash
# 回滾到上一個版本
alembic downgrade -1

# 回滾到特定版本
alembic downgrade <revision_id>

# 查看遷移歷史
alembic history
```

### 遷移最佳實踐

1. **測試遷移**：在開發環境先測試遷移腳本
2. **備份資料**：執行遷移前先備份資料庫
3. **停機維護**：重大結構變更時考慮停機維護
4. **版本控制**：將遷移腳本納入版本控制

## 監控與維護

### 查看日誌

```bash
# 查看所有服務日誌
docker-compose logs -f

# 查看特定服務日誌
docker-compose logs -f api
docker-compose logs -f worker

# 查看最近 100 行日誌
docker-compose logs --tail=100 api
```

### 監控系統資源

```bash
# 查看容器資源使用情況
docker stats

# 查看磁碟使用情況
df -h

# 查看資料庫大小
docker-compose exec db psql -U user -d recruitment -c "SELECT pg_size_pretty(pg_database_size('recruitment'));"
```

### 清理舊資料

```bash
# 清理舊的匯出檔案（30 天前）
find ./exports -type f -mtime +30 -delete

# 清理舊的日誌檔案
find ./logs -type f -mtime +30 -delete

# 清理 Docker 未使用的資源
docker system prune -a
```

### 效能優化

**資料庫優化**

```sql
-- 分析資料庫
ANALYZE;

-- 重建索引
REINDEX DATABASE recruitment;

-- 清理死元組
VACUUM FULL;
```

**Redis 優化**

```bash
# 清理 Redis 快取
docker-compose exec redis redis-cli FLUSHDB

# 查看 Redis 記憶體使用
docker-compose exec redis redis-cli INFO memory
```

## 故障排除

### 常見問題

#### 1. 容器無法啟動

```bash
# 查看容器日誌
docker-compose logs <service-name>

# 檢查容器狀態
docker-compose ps

# 重新建立容器
docker-compose up -d --force-recreate <service-name>
```

#### 2. 資料庫連線失敗

```bash
# 檢查資料庫是否運行
docker-compose exec db pg_isready -U user

# 檢查資料庫連線
docker-compose exec api python -c "from app.database import engine; engine.connect()"

# 重啟資料庫
docker-compose restart db
```

#### 3. Celery Worker 無法處理任務

```bash
# 查看 Worker 日誌
docker-compose logs -f worker

# 檢查 Redis 連線
docker-compose exec worker python -c "from redis import Redis; r = Redis.from_url('redis://redis:6379/0'); print(r.ping())"

# 重啟 Worker
docker-compose restart worker
```

#### 4. 爬蟲被封鎖

- 增加請求延遲：調整 `SCRAPING_MIN_DELAY` 和 `SCRAPING_MAX_DELAY`
- 輪換 User-Agent：增加更多 `SCRAPING_USER_AGENTS`
- 使用代理 IP（需額外配置）

#### 5. 記憶體不足

```bash
# 查看記憶體使用
docker stats

# 減少 Worker 並行數
# 在 .env 中設定: TASK_MAX_WORKERS=2

# 重啟服務
docker-compose restart worker
```

### 除錯模式

啟用除錯模式以獲取更詳細的日誌：

```bash
# 在 .env 中設定
DEBUG=true
LOG_LEVEL=DEBUG

# 重啟服務
docker-compose restart api worker
```

## 備份與恢復

### 資料庫備份

**自動備份腳本**

建立 `scripts/backup.sh`：

```bash
#!/bin/bash

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/recruitment_$TIMESTAMP.sql"

# 建立備份目錄
mkdir -p $BACKUP_DIR

# 執行備份
docker-compose exec -T db pg_dump -U user recruitment > $BACKUP_FILE

# 壓縮備份
gzip $BACKUP_FILE

# 刪除 30 天前的備份
find $BACKUP_DIR -type f -mtime +30 -delete

echo "備份完成: ${BACKUP_FILE}.gz"
```

**設定定時備份**

```bash
# 編輯 crontab
crontab -e

# 每天凌晨 2 點執行備份
0 2 * * * /path/to/scripts/backup.sh
```

### 資料庫恢復

```bash
# 停止服務
docker-compose stop api worker

# 恢復資料庫
gunzip -c backups/recruitment_20240101_020000.sql.gz | docker-compose exec -T db psql -U user recruitment

# 重啟服務
docker-compose start api worker
```

### 完整系統備份

```bash
# 備份資料庫
./scripts/backup.sh

# 備份匯出檔案
tar -czf exports_backup.tar.gz ./exports

# 備份日誌
tar -czf logs_backup.tar.gz ./logs

# 備份環境配置
cp .env .env.backup
```

## 安全建議

1. **使用強密碼**：資料庫和 Redis 使用強隨機密碼
2. **限制網路存取**：使用防火牆限制對資料庫和 Redis 的直接存取
3. **定期更新**：定期更新 Docker 映像和依賴套件
4. **啟用 SSL/TLS**：生產環境必須使用 HTTPS
5. **監控日誌**：定期檢查錯誤日誌和異常活動
6. **備份策略**：建立定期備份並測試恢復流程
7. **最小權限原則**：資料庫使用者僅授予必要權限

## 擴展部署

### 水平擴展

**增加 Worker 數量**

```bash
# 在 docker-compose.yml 中增加 Worker 實例
docker-compose up -d --scale worker=4
```

**資料庫讀寫分離**

配置 PostgreSQL 主從複製，讀取操作使用從庫。

### 負載平衡

使用 Nginx 或 HAProxy 進行負載平衡：

```nginx
upstream api_cluster {
    server api1:8000;
    server api2:8000;
    server api3:8000;
}
```

## 聯絡支援

如遇到部署問題，請聯絡技術支援團隊。
