# DigitalOcean 部署故障排除指南

## 常見問題與解決方案

### 🔴 問題 1: 資料庫容器無法啟動 (container recruitment-db is unhealthy)

**錯誤訊息**:
```
Container recruitment-db  Error
dependency failed to start: container recruitment-db is unhealthy
```

**原因**:
1. 健康檢查配置不正確，環境變數無法正確解析
2. 資料庫啟動時間不足
3. 資料庫初始化失敗

**解決方案**:

#### 方案 1: 檢查健康檢查配置
確保 `docker-compose.prod.yml` 中的健康檢查使用容器內部的環境變數：

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
  interval: 10s
  timeout: 5s
  retries: 10
  start_period: 30s
```

#### 方案 2: 手動檢查資料庫狀態
```bash
# SSH 連接到 Droplet
ssh root@YOUR_DROPLET_IP

# 進入專案目錄
cd /opt/apps

# 載入環境變數
source .env

# 檢查資料庫容器日誌
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs db

# 手動測試資料庫連接
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec db pg_isready -U $DB_USER -d $DB_NAME

# 檢查資料庫容器狀態
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps db
```

#### 方案 3: 重新初始化資料庫
```bash
# 停止所有服務
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# 刪除資料庫 Volume（⚠️ 會刪除所有資料）
docker volume rm apps_postgres_data

# 重新啟動服務
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 等待資料庫啟動
sleep 30

# 檢查狀態
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

#### 方案 4: 檢查環境變數
```bash
# 檢查 .env 文件
cat /opt/apps/.env | grep DB_

# 確認環境變數格式正確
# 應該看到：
# DB_USER=recruitment_user
# DB_PASSWORD=your_password_here
# DB_NAME=recruitment_db
```

---

### 🟡 問題 2: 服務依賴資料庫但資料庫未就緒

**錯誤訊息**:
```
Error response from daemon: dependency failed to start
```

**解決方案**:

1. **增加啟動等待時間**:
   在 `docker-compose.prod.yml` 中增加 `start_period`:
   ```yaml
   healthcheck:
     start_period: 30s  # 給資料庫 30 秒啟動時間
   ```

2. **手動等待資料庫就緒**:
   ```bash
   # 等待資料庫完全啟動
   for i in {1..30}; do
       if docker compose exec db pg_isready -U $DB_USER -d $DB_NAME; then
           echo "資料庫已就緒"
           break
       fi
       echo "等待中... ($i/30)"
       sleep 2
   done
   ```

---

### 🟡 問題 3: 環境變數未正確載入

**錯誤訊息**:
```
Error: environment variable DB_USER is not set
```

**解決方案**:

1. **確認 .env 文件存在**:
   ```bash
   ls -la /opt/apps/.env
   ```

2. **檢查 .env 文件內容**:
   ```bash
   cat /opt/apps/.env
   ```

3. **手動載入環境變數**:
   ```bash
   cd /opt/apps
   set -a
   source .env
   set +a
   
   # 驗證變數
   echo $DB_USER
   echo $DB_NAME
   ```

4. **在 Docker Compose 中明確指定 .env 文件**:
   ```bash
   docker compose --env-file .env -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

---

### 🟡 問題 4: 記憶體不足

**錯誤訊息**:
```
OOMKilled: Container killed due to out of memory
```

**解決方案**:

1. **檢查記憶體使用**:
   ```bash
   free -h
   docker stats
   ```

2. **減少 Worker 數量**:
   編輯 `.env`:
   ```bash
   TASK_MAX_WORKERS=4  # 從 10 減少到 4
   ```

3. **升級 Droplet**:
   - 從 2GB RAM 升級到 4GB RAM
   - 或從 1 CPU 升級到 2 CPU

---

### 🟡 問題 5: 磁碟空間不足

**錯誤訊息**:
```
No space left on device
```

**解決方案**:

1. **檢查磁碟使用**:
   ```bash
   df -h
   ```

2. **清理 Docker 資源**:
   ```bash
   # 清理未使用的映像和容器
   docker system prune -a
   
   # 清理未使用的 Volume
   docker volume prune
   ```

3. **清理日誌**:
   ```bash
   # 清理舊日誌
   find /opt/apps/logs -name "*.log" -mtime +7 -delete
   ```

---

### 🟡 問題 6: 網路連接問題

**錯誤訊息**:
```
Error: connection refused
```

**解決方案**:

1. **檢查防火牆**:
   ```bash
   ufw status
   ufw allow 8000/tcp
   ufw allow 3000/tcp
   ```

2. **檢查服務是否運行**:
   ```bash
   docker compose ps
   ```

3. **檢查端口是否被占用**:
   ```bash
   netstat -tulpn | grep :8000
   netstat -tulpn | grep :3000
   ```

---

## 診斷步驟

### 步驟 1: 檢查服務狀態
```bash
cd /opt/apps
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

### 步驟 2: 查看日誌
```bash
# 查看所有服務日誌
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs

# 查看特定服務日誌
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs db
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs api
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs worker
```

### 步驟 3: 檢查資源使用
```bash
# 系統資源
htop

# Docker 容器資源
docker stats

# 磁碟空間
df -h
```

### 步驟 4: 測試連接
```bash
# 測試資料庫
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec db psql -U $DB_USER -d $DB_NAME -c "SELECT 1;"

# 測試 Redis
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec redis redis-cli ping

# 測試 API
curl http://localhost:8000/health
```

---

## 快速修復命令

### 完全重置部署
```bash
# ⚠️ 警告：這會刪除所有資料
cd /opt/apps
docker compose -f docker-compose.yml -f docker-compose.prod.yml down -v
docker system prune -a
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### 僅重啟服務
```bash
cd /opt/apps
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart
```

### 重新建置並啟動
```bash
cd /opt/apps
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
docker compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## 預防措施

1. **定期備份資料庫**:
   ```bash
   # 創建備份腳本
   cat > /opt/backups/backup.sh << 'EOF'
   #!/bin/bash
   BACKUP_DIR="/opt/backups"
   DATE=$(date +%Y%m%d_%H%M%S)
   cd /opt/apps
   source .env
   docker compose exec -T db pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz
   find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete
   EOF
   chmod +x /opt/backups/backup.sh
   ```

2. **監控服務狀態**:
   ```bash
   # 設置定時檢查
   crontab -e
   # 添加：每 5 分鐘檢查一次
   */5 * * * * cd /opt/apps && docker compose ps | grep -q "Up (healthy)" || echo "Service down" | mail -s "Service Alert" your-email@example.com
   ```

3. **設定日誌輪替**:
   ```bash
   # 創建日誌輪替配置
   cat > /etc/logrotate.d/recruitment << 'EOF'
   /opt/apps/logs/*.log {
       daily
       rotate 7
       compress
       delaycompress
       missingok
       notifempty
   }
   EOF
   ```

---

## 獲取幫助

如果以上方法都無法解決問題：

1. **收集診斷資訊**:
   ```bash
   # 創建診斷報告
   cat > /tmp/diagnostic_report.txt << EOF
   === System Info ===
   $(uname -a)
   $(free -h)
   $(df -h)
   
   === Docker Info ===
   $(docker --version)
   $(docker compose version)
   $(docker compose ps)
   
   === Service Logs ===
   $(docker compose logs --tail 50)
   
   === Environment ===
   $(cat .env | grep -v PASSWORD)
   EOF
   ```

2. **查看完整日誌**:
   ```bash
   docker compose logs > /tmp/full_logs.txt
   ```

3. **檢查 DigitalOcean 控制台**:
   - 查看 Droplet 的資源使用情況
   - 檢查是否有系統級錯誤
   - 查看網路流量

---

## 更新記錄

- **2025-01-XX**: 修復資料庫健康檢查配置問題
- **2025-01-XX**: 改進部署腳本的環境變數處理
- **2025-01-XX**: 增加啟動等待時間和重試機制

