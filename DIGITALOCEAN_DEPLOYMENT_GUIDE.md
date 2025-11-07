# DigitalOcean 部署完整指南

## 概述

使用 DigitalOcean Droplet 部署慈濟大學招生通路自動開發系統，使用 Docker Compose 一鍵部署。

## 成本

- **Droplet**: $12/月 (2GB RAM, 1 CPU, 50GB SSD)
- **總成本**: $12/月

## 部署步驟

### 階段 1: 創建 Droplet

#### 1.1 登入 DigitalOcean
訪問: https://cloud.digitalocean.com/

#### 1.2 創建新 Droplet
1. 點擊 "Create" → "Droplets"
2. 選擇配置：

**映像 (Image)**:
```
選擇: Ubuntu 22.04 LTS x64
```

**Droplet 大小 (Size)**:
```
推薦: Basic
CPU: Regular
RAM: 2GB
價格: $12/月
```

**資料中心 (Datacenter)**:
```
推薦: Singapore (最接近台灣)
或: San Francisco (美國西岸)
```

**驗證方式 (Authentication)**:
```
選項 1: SSH Key (推薦)
選項 2: Password
```

**主機名稱 (Hostname)**:
```
tcu-recruitment-system
```

#### 1.3 創建 Droplet
點擊 "Create Droplet"，等待 1-2 分鐘

### 階段 2: 連接到 Droplet

#### 2.1 獲取 IP 地址
```
在 DigitalOcean 控制台複製 Droplet 的 IP 地址
例如: 159.89.123.456
```

#### 2.2 SSH 連接
```bash
# 使用 SSH Key
ssh root@159.89.123.456

# 或使用密碼
ssh root@159.89.123.456
# 輸入密碼
```

### 階段 3: 安裝必要軟體

#### 3.1 更新系統
```bash
apt update && apt upgrade -y
```

#### 3.2 安裝 Docker
```bash
# 安裝 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 啟動 Docker
systemctl start docker
systemctl enable docker

# 驗證安裝
docker --version
```

#### 3.3 安裝 Docker Compose
```bash
# 安裝 Docker Compose
apt install docker-compose-plugin -y

# 驗證安裝
docker compose version
```

#### 3.4 安裝 Git
```bash
apt install git -y
git --version
```

### 階段 4: 部署應用程式

#### 4.1 克隆專案
```bash
# 創建應用目錄
mkdir -p /opt/apps
cd /opt/apps

# 克隆專案（替換為你的 Git 倉庫）
git clone https://github.com/your-username/recruitment-system.git
cd recruitment-system
```

#### 4.2 配置環境變數
```bash
# 複製環境變數範本
cp .env.example .env

# 編輯環境變數
nano .env
```

**重要環境變數**:
```bash
# 資料庫配置
DB_USER=recruitment_user
DB_PASSWORD=your_secure_password_here  # 改成強密碼
DB_NAME=recruitment_db

# Redis 配置
REDIS_PORT=6379

# API 配置
API_PORT=8000
API_HOST=0.0.0.0
CORS_ORIGINS=["http://your-domain.com","http://159.89.123.456:3000"]

# Celery 配置
TASK_MAX_WORKERS=10
TASK_TIMEOUT=300

# Google API (可選但推薦)
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_google_cse_id

# 日誌配置
LOG_LEVEL=INFO

# 爬蟲配置
SCRAPING_HEADLESS=true
RATE_LIMIT_ENABLED=true
```

**儲存並退出**: `Ctrl+X`, `Y`, `Enter`

#### 4.3 創建必要目錄
```bash
# 創建資料目錄
mkdir -p exports logs

# 設定權限
chmod 755 exports logs
```

#### 4.4 啟動服務
```bash
# 建置並啟動所有服務
docker compose up -d --build

# 查看服務狀態
docker compose ps
```

**預期輸出**:
```
NAME                   STATUS          PORTS
recruitment-api        Up              0.0.0.0:8000->8000/tcp
recruitment-worker     Up              
recruitment-beat       Up              
recruitment-db         Up (healthy)    0.0.0.0:5433->5432/tcp
recruitment-redis      Up (healthy)    0.0.0.0:6379->6379/tcp
recruitment-frontend   Up              0.0.0.0:3000->3000/tcp
```

#### 4.5 執行資料庫遷移
```bash
# 執行 Alembic 遷移
docker compose exec api alembic upgrade head

# 驗證遷移
docker compose exec db psql -U recruitment_user -d recruitment_db -c "\dt"
```

### 階段 5: 配置防火牆

#### 5.1 安裝 UFW
```bash
apt install ufw -y
```

#### 5.2 配置防火牆規則
```bash
# 允許 SSH
ufw allow 22/tcp

# 允許 HTTP
ufw allow 80/tcp

# 允許 HTTPS
ufw allow 443/tcp

# 允許 API (暫時，後面會用 Nginx 代理)
ufw allow 8000/tcp

# 允許前端 (暫時)
ufw allow 3000/tcp

# 啟用防火牆
ufw enable

# 查看狀態
ufw status
```

### 階段 6: 配置 Nginx 反向代理（可選但推薦）

#### 6.1 安裝 Nginx
```bash
apt install nginx -y
systemctl start nginx
systemctl enable nginx
```

#### 6.2 配置 Nginx
```bash
# 創建配置文件
nano /etc/nginx/sites-available/recruitment
```

**Nginx 配置**:
```nginx
# API 後端
server {
    listen 80;
    server_name api.your-domain.com;  # 或使用 IP

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# 前端
server {
    listen 80;
    server_name your-domain.com;  # 或使用 IP

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

#### 6.3 啟用配置
```bash
# 創建符號連結
ln -s /etc/nginx/sites-available/recruitment /etc/nginx/sites-enabled/

# 測試配置
nginx -t

# 重新載入 Nginx
systemctl reload nginx
```

#### 6.4 配置 SSL (使用 Let's Encrypt)
```bash
# 安裝 Certbot
apt install certbot python3-certbot-nginx -y

# 獲取 SSL 證書
certbot --nginx -d your-domain.com -d api.your-domain.com

# 自動續期
certbot renew --dry-run
```

### 階段 7: 驗證部署

#### 7.1 檢查服務狀態
```bash
# 查看所有容器
docker compose ps

# 查看日誌
docker compose logs -f --tail 50

# 查看特定服務日誌
docker compose logs api -f
docker compose logs worker -f
```

#### 7.2 測試 API
```bash
# 測試健康檢查
curl http://localhost:8000/

# 測試 API 端點
curl http://localhost:8000/api/tasks

# 從外部測試
curl http://159.89.123.456:8000/
```

#### 7.3 測試前端
```bash
# 在瀏覽器中訪問
http://159.89.123.456:3000
```

#### 7.4 測試任務執行
```bash
# 創建測試任務
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "country": "MY",
    "keyword": "University",
    "city": "Kuala Lumpur",
    "target_platforms": ["website"],
    "max_results": 10
  }'

# 查看任務狀態
curl http://localhost:8000/api/tasks
```

### 階段 8: 設定自動備份

#### 8.1 創建備份腳本
```bash
# 創建備份目錄
mkdir -p /opt/backups

# 創建備份腳本
nano /opt/backups/backup.sh
```

**備份腳本內容**:
```bash
#!/bin/bash

# 設定變數
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_CONTAINER="recruitment-db"
DB_USER="recruitment_user"
DB_NAME="recruitment_db"

# 創建備份
docker compose -f /opt/apps/recruitment-system/docker-compose.yml \
  exec -T db pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# 保留最近 7 天的備份
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: db_backup_$DATE.sql.gz"
```

#### 8.2 設定權限
```bash
chmod +x /opt/backups/backup.sh
```

#### 8.3 設定 Cron 定時任務
```bash
# 編輯 crontab
crontab -e

# 添加每天凌晨 2 點備份
0 2 * * * /opt/backups/backup.sh >> /opt/backups/backup.log 2>&1
```

### 階段 9: 設定監控

#### 9.1 安裝監控工具
```bash
# 安裝 htop
apt install htop -y

# 安裝 docker stats
# (已包含在 Docker 中)
```

#### 9.2 監控命令
```bash
# 查看系統資源
htop

# 查看 Docker 容器資源使用
docker stats

# 查看磁碟使用
df -h

# 查看記憶體使用
free -h
```

#### 9.3 設定日誌輪替
```bash
# 創建日誌輪替配置
nano /etc/logrotate.d/recruitment
```

**日誌輪替配置**:
```
/opt/apps/recruitment-system/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
```

### 階段 10: 維護和更新

#### 10.1 更新應用程式
```bash
cd /opt/apps/recruitment-system

# 拉取最新程式碼
git pull origin main

# 重新建置並重啟
docker compose down
docker compose up -d --build

# 執行遷移（如果有）
docker compose exec api alembic upgrade head
```

#### 10.2 查看日誌
```bash
# 查看所有日誌
docker compose logs -f

# 查看特定服務
docker compose logs api -f
docker compose logs worker -f
docker compose logs beat -f
```

#### 10.3 重啟服務
```bash
# 重啟所有服務
docker compose restart

# 重啟特定服務
docker compose restart api
docker compose restart worker
```

#### 10.4 清理資源
```bash
# 清理未使用的 Docker 映像
docker system prune -a

# 清理未使用的 Volume
docker volume prune
```

## 故障排除

### 問題 1: 容器無法啟動
```bash
# 查看日誌
docker compose logs [service-name]

# 檢查配置
docker compose config

# 重新建置
docker compose down
docker compose up -d --build
```

### 問題 2: 資料庫連接失敗
```bash
# 檢查資料庫容器
docker compose ps db

# 測試連接
docker compose exec db psql -U recruitment_user -d recruitment_db

# 檢查環境變數
docker compose exec api env | grep DATABASE
```

### 問題 3: Worker 不執行任務
```bash
# 檢查 Worker 日誌
docker compose logs worker -f

# 檢查 Redis 連接
docker compose exec worker python -c "
from app.celery_app import celery_app
print(celery_app.control.inspect().active())
"

# 重啟 Worker
docker compose restart worker
```

### 問題 4: 記憶體不足
```bash
# 查看記憶體使用
free -h
docker stats

# 減少 Worker 數量
# 編輯 .env
TASK_MAX_WORKERS=5

# 重啟
docker compose restart worker
```

### 問題 5: 磁碟空間不足
```bash
# 查看磁碟使用
df -h

# 清理 Docker
docker system prune -a --volumes

# 清理日誌
find /opt/apps/recruitment-system/logs -name "*.log" -mtime +7 -delete
```

## 安全建議

### 1. 更改預設密碼
```bash
# 更改資料庫密碼
# 編輯 .env
DB_PASSWORD=your_very_strong_password_here

# 重新建置
docker compose down
docker compose up -d
```

### 2. 限制 SSH 訪問
```bash
# 編輯 SSH 配置
nano /etc/ssh/sshd_config

# 禁用 root 登入
PermitRootLogin no

# 只允許特定用戶
AllowUsers your_username

# 重啟 SSH
systemctl restart sshd
```

### 3. 設定 Fail2Ban
```bash
# 安裝 Fail2Ban
apt install fail2ban -y

# 啟動服務
systemctl start fail2ban
systemctl enable fail2ban
```

### 4. 定期更新系統
```bash
# 設定自動更新
apt install unattended-upgrades -y
dpkg-reconfigure -plow unattended-upgrades
```

## 效能優化

### 1. 調整 Worker 數量
```bash
# 根據 CPU 核心數調整
# 2 核心 → 4-6 workers
# 4 核心 → 8-12 workers

# 編輯 .env
TASK_MAX_WORKERS=8
```

### 2. 啟用 Redis 持久化
```bash
# 編輯 docker-compose.yml
redis:
  command: redis-server --appendonly yes
```

### 3. 優化 PostgreSQL
```bash
# 編輯 docker-compose.yml
db:
  environment:
    - POSTGRES_SHARED_BUFFERS=256MB
    - POSTGRES_EFFECTIVE_CACHE_SIZE=1GB
```

## 成本優化

### 升級 Droplet（如果需要）
```
$12/月: 2GB RAM, 1 CPU (當前)
$18/月: 2GB RAM, 2 CPU (更快)
$24/月: 4GB RAM, 2 CPU (更多 Workers)
```

### 使用 Snapshot 備份
```
成本: $0.05/GB/月
建議: 每週創建一次 Snapshot
```

## 監控儀表板（可選）

### 安裝 Portainer
```bash
docker volume create portainer_data

docker run -d \
  -p 9000:9000 \
  --name portainer \
  --restart always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  portainer/portainer-ce

# 訪問: http://159.89.123.456:9000
```

## 總結

### 部署完成檢查清單

- [ ] Droplet 已創建
- [ ] Docker 和 Docker Compose 已安裝
- [ ] 專案已克隆
- [ ] 環境變數已配置
- [ ] 服務已啟動
- [ ] 資料庫遷移已執行
- [ ] 防火牆已配置
- [ ] Nginx 已配置（可選）
- [ ] SSL 證書已安裝（可選）
- [ ] 備份已設定
- [ ] 監控已設定

### 訪問應用程式

- **前端**: http://your-ip:3000 或 https://your-domain.com
- **API**: http://your-ip:8000 或 https://api.your-domain.com
- **API 文件**: http://your-ip:8000/docs

### 維護命令速查

```bash
# 查看狀態
docker compose ps

# 查看日誌
docker compose logs -f

# 重啟服務
docker compose restart

# 更新應用
git pull && docker compose up -d --build

# 備份資料庫
/opt/backups/backup.sh

# 查看資源使用
docker stats
```

### 支援

如果遇到問題：
1. 查看日誌: `docker compose logs -f`
2. 檢查服務狀態: `docker compose ps`
3. 查看系統資源: `htop` 或 `docker stats`
4. 參考故障排除章節

**部署成功！** 🎉

