#!/bin/bash

# 手動部署腳本 - 使用現有 Droplet
# 慈濟大學招生通路自動開發系統

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Droplet IP
DROPLET_IP="159.223.69.74"

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

# 函數：測試 SSH 連接
test_ssh() {
    print_info "測試 SSH 連接到 Droplet..."
    if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@${DROPLET_IP} "echo 'SSH 連接成功'" &> /dev/null; then
        print_success "SSH 連接成功"
        return 0
    else
        print_error "SSH 連接失敗，請檢查："
        echo "  1. Droplet IP 是否正確: ${DROPLET_IP}"
        echo "  2. SSH Key 是否已配置"
        echo "  3. 防火牆是否允許 SSH (端口 22)"
        return 1
    fi
}

# 函數：部署應用程式
deploy_application() {
    print_info "部署應用程式到 Droplet..."
    
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
        --exclude='.droplet_ip' \
        .
    
    # 上傳到 Droplet
    print_info "上傳專案文件到 Droplet..."
    scp /tmp/recruitment-system.tar.gz root@${DROPLET_IP}:/opt/apps/
    
    # 解壓並配置
    ssh root@${DROPLET_IP} << 'ENDSSH'
        set -e
        cd /opt/apps
        
        # 備份現有文件（如果存在）
        if [ -d "recruitment-system" ]; then
            echo "備份現有文件..."
            mv recruitment-system recruitment-system.backup.$(date +%Y%m%d_%H%M%S)
        fi
        
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
    DB_USER="recruitment_user"
    DB_NAME="recruitment_db"
    
    # 創建 .env 文件
    cat > /tmp/.env << EOF
# 資料庫配置
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=${DB_NAME}

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
    
    # 保存變數供後續使用
    export DB_PASSWORD
    export DB_USER
    export DB_NAME
}

# 函數：啟動服務
start_services() {
    print_info "啟動服務..."
    
    ssh root@${DROPLET_IP} << ENDSSH
        set -e
        cd /opt/apps
        
        # 載入環境變數
        set -a
        source .env
        set +a
        
        # 停止現有服務（如果存在）
        echo "停止現有服務..."
        docker compose -f docker-compose.yml -f docker-compose.prod.yml down 2>/dev/null || true
        
        # 建置並啟動服務
        echo "建置 Docker 映像..."
        docker compose -f docker-compose.yml -f docker-compose.prod.yml build
        
        echo "啟動服務..."
        docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
        
        # 等待資料庫完全啟動
        echo "等待資料庫完全啟動..."
        sleep 30
        
        # 檢查資料庫健康狀態
        echo "檢查資料庫健康狀態..."
        for i in {1..30}; do
            if docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T db pg_isready -U \$DB_USER -d \$DB_NAME &> /dev/null; then
                echo "資料庫已就緒"
                break
            fi
            echo "等待資料庫啟動... (\$i/30)"
            sleep 2
        done
        
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
    
    ssh root@${DROPLET_IP} << ENDSSH
        set -e
        cd /opt/apps
        
        # 載入環境變數
        set -a
        source .env
        set +a
        
        # 等待資料庫準備就緒
        echo "等待資料庫準備就緒..."
        for i in {1..30}; do
            if docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T db pg_isready -U \$DB_USER -d \$DB_NAME &> /dev/null; then
                echo "資料庫已就緒，可以執行遷移"
                break
            fi
            echo "等待資料庫準備... (\$i/30)"
            sleep 2
        done
        
        # 執行遷移
        echo "執行 Alembic 遷移..."
        docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T api alembic upgrade head
        
        echo "資料庫遷移完成！"
ENDSSH
    
    print_success "資料庫遷移完成"
}

# 函數：顯示部署資訊
show_deployment_info() {
    print_success "========================================="
    print_success "部署完成！"
    print_success "========================================="
    echo ""
    print_info "Droplet 資訊:"
    echo "  IP 地址: ${DROPLET_IP}"
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
    echo "  查看日誌: ssh root@${DROPLET_IP} 'cd /opt/apps && docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f'"
    echo "  重啟服務: ssh root@${DROPLET_IP} 'cd /opt/apps && docker compose -f docker-compose.yml -f docker-compose.prod.yml restart'"
    echo "  查看狀態: ssh root@${DROPLET_IP} 'cd /opt/apps && docker compose -f docker-compose.yml -f docker-compose.prod.yml ps'"
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
    print_info "DigitalOcean 手動部署腳本"
    print_info "慈濟大學招生通路自動開發系統"
    print_info "========================================="
    echo ""
    
    # 測試 SSH 連接
    if ! test_ssh; then
        exit 1
    fi
    
    # 執行部署步驟
    deploy_application
    configure_environment
    start_services
    run_migrations
    
    # 顯示部署資訊
    show_deployment_info
}

# 執行主函數
main

