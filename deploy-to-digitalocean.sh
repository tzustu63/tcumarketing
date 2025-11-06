#!/bin/bash

# DigitalOcean 自動部署腳本
# 慈濟大學招生通路自動開發系統

set -e  # 遇到錯誤立即退出

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置變數
DROPLET_NAME="tcu-recruitment-system"
DROPLET_SIZE="s-2vcpu-2gb"  # 2GB RAM, 2 CPU, $18/月
DROPLET_IMAGE="ubuntu-22-04-x64"
DROPLET_REGION="sgp1"  # 新加坡
SSH_KEY_NAME="default"

# 函數：打印訊息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 函數：檢查 doctl 是否已安裝
check_doctl() {
    if ! command -v doctl &> /dev/null; then
        print_error "doctl 未安裝，請先安裝 DigitalOcean CLI"
        echo "安裝方法: brew install doctl"
        exit 1
    fi
    print_success "doctl 已安裝"
}

# 函數：檢查是否已登入
check_auth() {
    if ! doctl account get &> /dev/null; then
        print_error "未登入 DigitalOcean"
        echo "請執行: doctl auth init"
        exit 1
    fi
    print_success "已登入 DigitalOcean"
}

# 函數：列出可用的 SSH Keys
list_ssh_keys() {
    print_info "列出可用的 SSH Keys..."
    doctl compute ssh-key list
}

# 函數：創建 Droplet
create_droplet() {
    print_info "檢查 Droplet 是否已存在..."
    
    # 檢查是否已存在
    EXISTING_DROPLET=$(doctl compute droplet list --format Name --no-header | grep "^${DROPLET_NAME}$" || true)
    
    if [ -n "$EXISTING_DROPLET" ]; then
        print_warning "Droplet '${DROPLET_NAME}' 已存在"
        print_info "刪除現有 Droplet..."
        doctl compute droplet delete ${DROPLET_NAME} --force
        sleep 5
    fi
    
    print_info "創建新 Droplet..."
    print_info "名稱: ${DROPLET_NAME}"
    print_info "大小: ${DROPLET_SIZE}"
    print_info "區域: ${DROPLET_REGION}"
    print_info "映像: ${DROPLET_IMAGE}"
    
    # 獲取 SSH Key ID
    SSH_KEY_ID=$(doctl compute ssh-key list --format ID --no-header | head -n 1)
    
    if [ -z "$SSH_KEY_ID" ]; then
        print_error "未找到 SSH Key，請先添加 SSH Key"
        echo "添加方法: doctl compute ssh-key create my-key --public-key-file ~/.ssh/id_rsa.pub"
        exit 1
    fi
    
    # 創建 Droplet
    doctl compute droplet create ${DROPLET_NAME} \
        --size ${DROPLET_SIZE} \
        --image ${DROPLET_IMAGE} \
        --region ${DROPLET_REGION} \
        --ssh-keys ${SSH_KEY_ID} \
        --wait \
        --format ID,Name,PublicIPv4,Status
    
    print_success "Droplet 創建成功！"
}

# 函數：獲取 Droplet IP
get_droplet_ip() {
    print_info "獲取 Droplet IP 地址..."
    DROPLET_IP=$(doctl compute droplet list --format Name,PublicIPv4 --no-header | grep "^${DROPLET_NAME}" | awk '{print $2}')
    
    if [ -z "$DROPLET_IP" ]; then
        print_error "無法獲取 Droplet IP"
        exit 1
    fi
    
    print_success "Droplet IP: ${DROPLET_IP}"
    echo "$DROPLET_IP" > .droplet_ip
}

# 函數：等待 Droplet 準備就緒
wait_for_droplet() {
    print_info "等待 Droplet 準備就緒..."
    sleep 30
    
    print_info "測試 SSH 連接..."
    for i in {1..10}; do
        if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@${DROPLET_IP} "echo 'SSH 連接成功'" &> /dev/null; then
            print_success "SSH 連接成功"
            return 0
        fi
        print_info "等待 SSH 準備... (${i}/10)"
        sleep 10
    done
    
    print_error "SSH 連接失敗"
    exit 1
}

# 函數：安裝 Docker
install_docker() {
    print_info "在 Droplet 上安裝 Docker..."
    
    ssh root@${DROPLET_IP} << 'ENDSSH'
        set -e
        
        # 更新系統
        echo "更新系統..."
        apt-get update
        DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
        
        # 安裝 Docker
        echo "安裝 Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        
        # 啟動 Docker
        systemctl start docker
        systemctl enable docker
        
        # 安裝 Docker Compose
        echo "安裝 Docker Compose..."
        apt-get install -y docker-compose-plugin
        
        # 安裝 Git
        echo "安裝 Git..."
        apt-get install -y git
        
        # 驗證安裝
        docker --version
        docker compose version
        git --version
        
        echo "Docker 安裝完成！"
ENDSSH
    
    print_success "Docker 安裝完成"
}

# 函數：部署應用程式
deploy_application() {
    print_info "部署應用程式..."
    
    # 創建部署目錄
    ssh root@${DROPLET_IP} "mkdir -p /opt/apps"
    
    # 壓縮專案文件（排除不需要的文件）
    print_info "壓縮專案文件..."
    tar -czf /tmp/recruitment-system.tar.gz \
        --exclude='.git' \
        --exclude='node_modules' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.env' \
        --exclude='postgres_data' \
        --exclude='redis_data' \
        --exclude='exports/*' \
        --exclude='logs/*' \
        .
    
    # 上傳到 Droplet
    print_info "上傳專案文件到 Droplet..."
    scp /tmp/recruitment-system.tar.gz root@${DROPLET_IP}:/opt/apps/
    
    # 解壓並配置
    ssh root@${DROPLET_IP} << 'ENDSSH'
        set -e
        cd /opt/apps
        
        # 解壓
        echo "解壓專案文件..."
        tar -xzf recruitment-system.tar.gz
        rm recruitment-system.tar.gz
        
        # 創建必要目錄
        mkdir -p exports logs
        chmod 755 exports logs
        
        echo "專案文件部署完成！"
ENDSSH
    
    print_success "應用程式部署完成"
}

# 函數：配置環境變數
configure_environment() {
    print_info "配置環境變數..."
    
    # 生成隨機密碼
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    
    # 創建 .env 文件
    cat > /tmp/.env << EOF
# 資料庫配置
DB_USER=recruitment_user
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=recruitment_db

# Redis 配置
REDIS_PORT=6379

# API 配置
API_PORT=8000
API_HOST=0.0.0.0
CORS_ORIGINS=["http://${DROPLET_IP}:3000","http://localhost:3000"]

# Celery 配置
TASK_MAX_WORKERS=10
TASK_TIMEOUT=300

# Google API (請手動設定)
GOOGLE_API_KEY=
GOOGLE_CSE_ID=

# 日誌配置
LOG_LEVEL=INFO

# 爬蟲配置
SCRAPING_HEADLESS=true
RATE_LIMIT_ENABLED=true
RATE_LIMIT_MAX_REQUESTS_PER_DOMAIN=10
RATE_LIMIT_DOMAIN_TIME_WINDOW=60
RATE_LIMIT_MIN_REQUEST_INTERVAL=2.0
SCRAPING_MIN_DELAY=2
SCRAPING_MAX_DELAY=5

# 前端配置
REACT_APP_API_URL=http://${DROPLET_IP}:8000
NODE_ENV=production
EOF
    
    # 上傳 .env 文件
    scp /tmp/.env root@${DROPLET_IP}:/opt/apps/.env
    
    print_success "環境變數配置完成"
    print_warning "資料庫密碼: ${DB_PASSWORD}"
    print_warning "請記住這個密碼！"
}

# 函數：啟動服務
start_services() {
    print_info "啟動服務..."
    
    ssh root@${DROPLET_IP} << 'ENDSSH'
        set -e
        cd /opt/apps
        
        # 建置並啟動服務
        echo "建置 Docker 映像..."
        docker compose -f docker-compose.yml -f docker-compose.prod.yml build
        
        echo "啟動服務..."
        docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
        
        # 等待服務啟動
        echo "等待服務啟動..."
        sleep 20
        
        # 檢查服務狀態
        echo "檢查服務狀態..."
        docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
        
        echo "服務啟動完成！"
ENDSSH
    
    print_success "服務啟動完成"
}

# 函數：執行資料庫遷移
run_migrations() {
    print_info "執行資料庫遷移..."
    
    ssh root@${DROPLET_IP} << 'ENDSSH'
        set -e
        cd /opt/apps
        
        # 等待資料庫準備就緒
        echo "等待資料庫準備就緒..."
        sleep 10
        
        # 執行遷移
        echo "執行 Alembic 遷移..."
        docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T api alembic upgrade head
        
        echo "資料庫遷移完成！"
ENDSSH
    
    print_success "資料庫遷移完成"
}

# 函數：配置防火牆
configure_firewall() {
    print_info "配置防火牆..."
    
    ssh root@${DROPLET_IP} << 'ENDSSH'
        set -e
        
        # 安裝 UFW
        apt-get install -y ufw
        
        # 配置規則
        ufw allow 22/tcp    # SSH
        ufw allow 80/tcp    # HTTP
        ufw allow 443/tcp   # HTTPS
        ufw allow 8000/tcp  # API
        ufw allow 3000/tcp  # Frontend
        
        # 啟用防火牆
        echo "y" | ufw enable
        
        # 查看狀態
        ufw status
        
        echo "防火牆配置完成！"
ENDSSH
    
    print_success "防火牆配置完成"
}

# 函數：顯示部署資訊
show_deployment_info() {
    print_success "========================================="
    print_success "部署完成！"
    print_success "========================================="
    echo ""
    print_info "Droplet 資訊:"
    echo "  名稱: ${DROPLET_NAME}"
    echo "  IP 地址: ${DROPLET_IP}"
    echo "  區域: ${DROPLET_REGION}"
    echo ""
    print_info "訪問地址:"
    echo "  前端: http://${DROPLET_IP}:3000"
    echo "  API: http://${DROPLET_IP}:8000"
    echo "  API 文件: http://${DROPLET_IP}:8000/docs"
    echo ""
    print_info "SSH 連接:"
    echo "  ssh root@${DROPLET_IP}"
    echo ""
    print_info "管理命令:"
    echo "  查看日誌: ssh root@${DROPLET_IP} 'cd /opt/apps && docker compose logs -f'"
    echo "  重啟服務: ssh root@${DROPLET_IP} 'cd /opt/apps && docker compose restart'"
    echo "  查看狀態: ssh root@${DROPLET_IP} 'cd /opt/apps && docker compose ps'"
    echo ""
    print_warning "重要提醒:"
    echo "  1. 請記住資料庫密碼（已顯示在上方）"
    echo "  2. 請設定 Google API Key（編輯 .env 文件）"
    echo "  3. 建議設定域名並配置 SSL"
    echo ""
}

# 主函數
main() {
    echo ""
    print_info "========================================="
    print_info "DigitalOcean 自動部署腳本"
    print_info "慈濟大學招生通路自動開發系統"
    print_info "========================================="
    echo ""
    
    # 檢查環境
    check_doctl
    check_auth
    
    # 顯示帳戶資訊
    print_info "帳戶資訊:"
    doctl account get
    echo ""
    
    # 確認部署（自動執行）
    print_info "開始自動部署..."
    
    # 執行部署步驟
    create_droplet
    get_droplet_ip
    wait_for_droplet
    install_docker
    deploy_application
    configure_environment
    start_services
    run_migrations
    configure_firewall
    
    # 顯示部署資訊
    show_deployment_info
}

# 執行主函數
main
