#!/bin/bash

# 在 Droplet 上執行的自動部署腳本
# 慈濟大學招生通路自動開發系統

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 檢查是否在正確目錄
if [ ! -f "docker-compose.yml" ]; then
    print_error "請在專案根目錄執行此腳本"
    exit 1
fi

print_info "========================================="
print_info "開始自動部署"
print_info "========================================="
echo ""

# 步驟 1: 解壓專案文件（如果使用上傳的文件）
if [ -f "/tmp/recruitment-system.tar.gz" ]; then
    print_info "發現上傳的文件，正在解壓..."
    tar -xzf /tmp/recruitment-system.tar.gz
    rm /tmp/recruitment-system.tar.gz
    print_success "文件解壓完成"
fi

# 步驟 2: 創建必要目錄
print_info "創建必要目錄..."
mkdir -p exports logs
chmod 755 exports logs
print_success "目錄創建完成"

# 步驟 3: 配置環境變數
print_info "配置環境變數..."

if [ ! -f ".env" ]; then
    # 生成隨機密碼
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    DB_USER="recruitment_user"
    DB_NAME="recruitment_db"
    
    # 創建 .env 文件
    cat > .env << EOF
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
    
    print_success "環境變數配置完成"
    print_warning "資料庫密碼: ${DB_PASSWORD}"
    print_warning "請記住這個密碼！"
else
    print_info ".env 文件已存在，跳過創建"
    # 載入現有環境變數
    set -a
    source .env
    set +a
    print_success "已載入現有環境變數"
fi

# 步驟 4: 停止現有服務
print_info "停止現有服務（如果存在）..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml down 2>/dev/null || true
print_success "現有服務已停止"

# 步驟 5: 建置 Docker 映像
print_info "建置 Docker 映像..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml build
print_success "Docker 映像建置完成"

# 步驟 6: 啟動服務
print_info "啟動服務..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
print_success "服務已啟動"

# 步驟 7: 等待資料庫啟動
print_info "等待資料庫啟動..."
sleep 30

print_info "檢查資料庫健康狀態..."
DB_READY=false
for i in {1..30}; do
    if docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T db pg_isready -U $DB_USER -d $DB_NAME &> /dev/null; then
        print_success "資料庫已就緒"
        DB_READY=true
        break
    fi
    print_info "等待資料庫啟動... ($i/30)"
    sleep 2
done

if [ "$DB_READY" = false ]; then
    print_error "資料庫啟動超時，請檢查日誌"
    docker compose -f docker-compose.yml -f docker-compose.prod.yml logs db
    exit 1
fi

# 步驟 8: 執行資料庫遷移
print_info "執行資料庫遷移..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T api alembic upgrade head
print_success "資料庫遷移完成"

# 步驟 9: 檢查服務狀態
print_info "檢查服務狀態..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# 步驟 10: 測試 API
print_info "測試 API..."
sleep 5
if curl -f http://localhost:8000/health &> /dev/null; then
    print_success "API 健康檢查通過"
else
    print_warning "API 健康檢查失敗，請檢查日誌"
    docker compose -f docker-compose.yml -f docker-compose.prod.yml logs api | tail -20
fi

# 完成
print_success "========================================="
print_success "部署完成！"
print_success "========================================="
echo ""
print_info "訪問地址:"
echo "  前端: http://${DROPLET_IP}:3000"
echo "  API: http://${DROPLET_IP}:8000"
echo "  API 文件: http://${DROPLET_IP}:8000/docs"
echo ""
print_info "管理命令:"
echo "  查看日誌: docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f"
echo "  重啟服務: docker compose -f docker-compose.yml -f docker-compose.prod.yml restart"
echo "  查看狀態: docker compose -f docker-compose.yml -f docker-compose.prod.yml ps"
echo ""

