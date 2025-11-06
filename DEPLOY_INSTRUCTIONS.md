# DigitalOcean 一鍵部署說明

## 準備工作

### ✅ 已完成
- [x] DigitalOcean CLI (doctl) 已安裝
- [x] 已登入 DigitalOcean 帳戶
- [x] 帳戶: tzustu@gmail.com
- [x] Droplet 限制: 15 個

### 📋 部署前檢查

1. **確認 SSH Key**
```bash
# 列出 SSH Keys
doctl compute ssh-key list

# 如果沒有，創建一個
ssh-keygen -t rsa -b 4096 -C "tzustu@gmail.com"
doctl compute ssh-key create my-key --public-key-file ~/.ssh/id_rsa.pub
```

2. **確認專案目錄**
```bash
# 確保在專案根目錄
pwd
# 應該顯示: /path/to/auto scraper for oga
```

3. **確認 Docker Compose 配置**
```bash
# 檢查 docker-compose.yml 是否存在
ls docker-compose.yml
```

## 部署步驟

### 方法 1: 一鍵自動部署（推薦）

```bash
# 執行部署腳本
./deploy-to-digitalocean.sh
```

**腳本會自動執行以下步驟**:
1. ✅ 檢查 doctl 和登入狀態
2. ✅ 創建 Droplet (2GB RAM, 新加坡)
3. ✅ 安裝 Docker 和 Docker Compose
4. ✅ 上傳專案文件
5. ✅ 配置環境變數
6. ✅ 啟動所有服務
7. ✅ 執行資料庫遷移
8. ✅ 配置防火牆

**預計時間**: 10-15 分鐘

### 方法 2: 手動部署

如果自動部署失敗，可以手動執行：

#### 步驟 1: 創建 Droplet
```bash
# 獲取 SSH Key ID
SSH_KEY_ID=$(doctl compute ssh-key list --format ID --no-header | head -n 1)

# 創建 Droplet
doctl compute droplet create tcu-recruitment-system \
    --size s-2vcpu-2gb \
    --image ubuntu-22-04-x64 \
    --region sgp1 \
    --ssh-keys $SSH_KEY_ID \
    --wait

# 獲取 IP
doctl compute droplet list --format Name,PublicIPv4
```

#### 步驟 2: SSH 連接
```bash
# 替換為你的 Droplet IP
DROPLET_IP="your_droplet_ip"
ssh root@$DROPLET_IP
```

#### 步驟 3: 安裝 Docker
```bash
# 在 Droplet 上執行
apt update && apt upgrade -y
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
apt install -y docker-compose-plugin git
```

#### 步驟 4: 部署應用
```bash
# 在本地執行（壓縮並上傳）
tar -czf /tmp/app.tar.gz \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    .

scp /tmp/app.tar.gz root@$DROPLET_IP:/opt/

# 在 Droplet 上執行
ssh root@$DROPLET_IP
cd /opt
tar -xzf app.tar.gz
cd auto\ scraper\ for\ oga  # 或你的專案目錄名稱
```

#### 步驟 5: 配置環境變數
```bash
# 在 Droplet 上執行
cp .env.example .env
nano .env

# 修改以下內容:
# - DB_PASSWORD (設定強密碼)
# - CORS_ORIGINS (添加 Droplet IP)
# - GOOGLE_API_KEY (如果有)
```

#### 步驟 6: 啟動服務
```bash
# 在 Droplet 上執行
docker compose up -d --build
docker compose ps
```

#### 步驟 7: 執行遷移
```bash
# 在 Droplet 上執行
docker compose exec api alembic upgrade head
```

## 部署配置

### Droplet 規格
```
名稱: tcu-recruitment-system
大小: s-2vcpu-2gb (2GB RAM, 2 CPU)
價格: $18/月
區域: sgp1 (新加坡)
映像: Ubuntu 22.04 LTS
```

### 為什麼選擇 2GB RAM？
- 1GB RAM 不夠運行所有服務
- 2GB RAM 可以穩定運行 10 個 Workers
- 性價比最好

### 可用區域
```bash
# 查看所有區域
doctl compute region list

# 推薦區域（亞洲）:
# - sgp1: 新加坡
# - blr1: 印度班加羅爾
# - syd1: 澳洲雪梨
```

## 部署後驗證

### 1. 檢查服務狀態
```bash
ssh root@$DROPLET_IP "cd /opt/apps && docker compose ps"
```

**預期輸出**:
```
NAME                   STATUS
recruitment-api        Up
recruitment-worker     Up
recruitment-beat       Up
recruitment-db         Up (healthy)
recruitment-redis      Up (healthy)
recruitment-frontend   Up
```

### 2. 測試 API
```bash
# 測試健康檢查
curl http://$DROPLET_IP:8000/

# 測試 API 端點
curl http://$DROPLET_IP:8000/api/tasks
```

### 3. 訪問前端
在瀏覽器中打開:
```
http://your_droplet_ip:3000
```

### 4. 查看日誌
```bash
# 查看所有日誌
ssh root@$DROPLET_IP "cd /opt/apps && docker compose logs -f"

# 查看特定服務
ssh root@$DROPLET_IP "cd /opt/apps && docker compose logs api -f"
```

## 常用管理命令

### SSH 連接
```bash
ssh root@$DROPLET_IP
```

### 查看服務狀態
```bash
ssh root@$DROPLET_IP "cd /opt/apps && docker compose ps"
```

### 重啟服務
```bash
# 重啟所有服務
ssh root@$DROPLET_IP "cd /opt/apps && docker compose restart"

# 重啟特定服務
ssh root@$DROPLET_IP "cd /opt/apps && docker compose restart api"
```

### 查看日誌
```bash
ssh root@$DROPLET_IP "cd /opt/apps && docker compose logs -f --tail 50"
```

### 更新應用
```bash
# 1. 在本地拉取最新程式碼
git pull

# 2. 重新部署
./deploy-to-digitalocean.sh
```

### 備份資料庫
```bash
ssh root@$DROPLET_IP "cd /opt/apps && docker compose exec -T db pg_dump -U recruitment_user recruitment_db | gzip > backup_$(date +%Y%m%d).sql.gz"
```

## 故障排除

### 問題 1: 部署腳本失敗
```bash
# 查看詳細錯誤
./deploy-to-digitalocean.sh 2>&1 | tee deploy.log

# 或手動執行每個步驟
```

### 問題 2: 無法 SSH 連接
```bash
# 檢查 Droplet 狀態
doctl compute droplet list

# 檢查防火牆
doctl compute firewall list

# 重啟 Droplet
doctl compute droplet-action reboot <droplet-id>
```

### 問題 3: 服務無法啟動
```bash
# SSH 到 Droplet
ssh root@$DROPLET_IP

# 查看日誌
cd /opt/apps
docker compose logs

# 重新建置
docker compose down
docker compose up -d --build
```

### 問題 4: 記憶體不足
```bash
# 升級 Droplet
doctl compute droplet-action resize <droplet-id> --size s-2vcpu-4gb --wait

# 或減少 Worker 數量
# 編輯 .env: TASK_MAX_WORKERS=5
```

## 成本管理

### 當前配置成本
```
Droplet (2GB): $18/月
備份 (20%):    $3.6/月
總計:          $21.6/月
```

### 降低成本
```bash
# 選項 1: 使用 1GB Droplet (不推薦)
# $12/月，但可能記憶體不足

# 選項 2: 不啟用備份
# 節省 $3.6/月，但需要手動備份

# 選項 3: 使用 Snapshot 代替備份
# $0.05/GB/月，更便宜
```

### 刪除 Droplet（停止計費）
```bash
# 列出所有 Droplet
doctl compute droplet list

# 刪除 Droplet
doctl compute droplet delete tcu-recruitment-system --force
```

## 安全建議

### 1. 更改 SSH 端口
```bash
ssh root@$DROPLET_IP
nano /etc/ssh/sshd_config
# 修改: Port 2222
systemctl restart sshd
```

### 2. 禁用 root 登入
```bash
# 創建新用戶
adduser admin
usermod -aG sudo admin

# 禁用 root
nano /etc/ssh/sshd_config
# 修改: PermitRootLogin no
```

### 3. 設定 Fail2Ban
```bash
apt install fail2ban -y
systemctl enable fail2ban
```

### 4. 定期更新
```bash
apt update && apt upgrade -y
docker compose pull
docker compose up -d
```

## 下一步

### 1. 設定域名（可選）
```bash
# 在 DigitalOcean 添加域名
doctl compute domain create your-domain.com

# 添加 A 記錄
doctl compute domain records create your-domain.com \
    --record-type A \
    --record-name @ \
    --record-data $DROPLET_IP
```

### 2. 配置 SSL（可選）
```bash
ssh root@$DROPLET_IP

# 安裝 Nginx 和 Certbot
apt install nginx certbot python3-certbot-nginx -y

# 獲取 SSL 證書
certbot --nginx -d your-domain.com
```

### 3. 設定監控（可選）
```bash
# 安裝 Portainer
docker run -d \
    -p 9000:9000 \
    --name portainer \
    --restart always \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v portainer_data:/data \
    portainer/portainer-ce
```

## 支援

如果遇到問題:
1. 查看 `deploy.log` 文件
2. 檢查 Docker 日誌
3. 參考 `DIGITALOCEAN_DEPLOYMENT_GUIDE.md`
4. 聯繫技術支援

## 總結

### 快速開始
```bash
# 1. 確認環境
doctl auth list

# 2. 執行部署
./deploy-to-digitalocean.sh

# 3. 訪問應用
# http://your_droplet_ip:3000
```

### 預計時間
- 部署: 10-15 分鐘
- 配置: 5 分鐘
- 總計: 15-20 分鐘

### 預計成本
- 第一個月: $18 (Droplet)
- 之後每月: $18-22

**準備好了嗎？執行 `./deploy-to-digitalocean.sh` 開始部署！** 🚀

