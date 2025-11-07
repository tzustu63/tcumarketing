#!/bin/bash
# Railway 快速指令腳本
# 使用方式：./railway-quick-commands.sh [指令]

set -e

# 專案 Token
export RAILWAY_TOKEN=5ff08d2d-64e7-44f0-ab91-d0f28adcf213

# 顏色輸出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 檢查 Railway CLI 是否已安裝
check_railway_cli() {
    if ! command -v railway &> /dev/null; then
        echo -e "${RED}❌ Railway CLI 未安裝${NC}"
        echo -e "${YELLOW}正在安裝 Railway CLI...${NC}"
        npm install -g @railway/cli
        echo -e "${GREEN}✅ Railway CLI 安裝完成${NC}"
    else
        echo -e "${GREEN}✅ Railway CLI 已安裝${NC}"
    fi
}

# 顯示幫助訊息
show_help() {
    echo -e "${BLUE}=== Railway 快速指令 ===${NC}\n"
    echo "使用方式: ./railway-quick-commands.sh [指令]"
    echo ""
    echo "可用指令："
    echo "  migrate       - 執行資料庫遷移"
    echo "  logs-api      - 查看 API 服務日誌"
    echo "  logs-worker   - 查看 Worker 服務日誌"
    echo "  logs-beat     - 查看 Beat 服務日誌"
    echo "  status        - 查看所有服務狀態"
    echo "  vars-api      - 查看 API 環境變數"
    echo "  vars-worker   - 查看 Worker 環境變數"
    echo "  deploy-api    - 重新部署 API 服務"
    echo "  deploy-worker - 重新部署 Worker 服務"
    echo "  deploy-beat   - 重新部署 Beat 服務"
    echo "  deploy-all    - 重新部署所有服務"
    echo "  shell         - 在 API 服務中開啟 shell"
    echo ""
}

# 執行資料庫遷移
run_migration() {
    echo -e "${BLUE}📦 執行資料庫遷移...${NC}"
    railway run --service tcu-api alembic upgrade head
    echo -e "${GREEN}✅ 遷移完成${NC}"
}

# 查看服務日誌
view_logs() {
    local service=$1
    echo -e "${BLUE}📋 查看 ${service} 服務日誌...${NC}"
    railway logs --service "$service"
}

# 查看服務狀態
view_status() {
    echo -e "${BLUE}📊 查看服務狀態...${NC}"
    railway status
}

# 查看環境變數
view_vars() {
    local service=$1
    echo -e "${BLUE}🔐 查看 ${service} 環境變數...${NC}"
    railway variables --service "$service"
}

# 重新部署服務
redeploy_service() {
    local service=$1
    echo -e "${YELLOW}🚀 重新部署 ${service} 服務...${NC}"
    railway up --service "$service"
    echo -e "${GREEN}✅ ${service} 部署已觸發${NC}"
}

# 重新部署所有服務
redeploy_all() {
    echo -e "${YELLOW}🚀 重新部署所有服務...${NC}"
    railway up --service tcu-api
    railway up --service tcu-worker
    railway up --service tcu-beat
    railway up --service tcu-frontend
    echo -e "${GREEN}✅ 所有服務部署已觸發${NC}"
}

# 開啟遠端 shell
open_shell() {
    echo -e "${BLUE}💻 開啟 API 服務 shell...${NC}"
    railway run --service tcu-api bash
}

# 主程式
main() {
    check_railway_cli

    case "${1:-help}" in
        migrate)
            run_migration
            ;;
        logs-api)
            view_logs "tcu-api"
            ;;
        logs-worker)
            view_logs "tcu-worker"
            ;;
        logs-beat)
            view_logs "tcu-beat"
            ;;
        logs-frontend)
            view_logs "tcu-frontend"
            ;;
        status)
            view_status
            ;;
        vars-api)
            view_vars "tcu-api"
            ;;
        vars-worker)
            view_vars "tcu-worker"
            ;;
        vars-beat)
            view_vars "tcu-beat"
            ;;
        deploy-api)
            redeploy_service "tcu-api"
            ;;
        deploy-worker)
            redeploy_service "tcu-worker"
            ;;
        deploy-beat)
            redeploy_service "tcu-beat"
            ;;
        deploy-frontend)
            redeploy_service "tcu-frontend"
            ;;
        deploy-all)
            redeploy_all
            ;;
        shell)
            open_shell
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}❌ 未知指令: $1${NC}\n"
            show_help
            exit 1
            ;;
    esac
}

main "$@"

