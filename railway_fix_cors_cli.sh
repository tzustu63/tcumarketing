#!/bin/bash

# Railway CLI 修復 CORS 腳本
# 此腳本會自動設置 API 服務的 CORS_ORIGINS 環境變數

set -e

echo "🔧 使用 Railway CLI 修復 CORS 問題"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 檢查 Railway CLI 是否已安裝
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI 未安裝${NC}"
    echo ""
    echo "請先安裝 Railway CLI："
    echo "npm install -g @railway/cli"
    exit 1
fi

# 檢查是否已登入
echo -e "${BLUE}📋 檢查登入狀態...${NC}"
if ! railway whoami &> /dev/null; then
    echo -e "${RED}❌ 未登入 Railway${NC}"
    echo ""
    echo "請先執行："
    echo "railway login"
    exit 1
fi

LOGGED_IN_USER=$(railway whoami | grep -o '[^ ]*@[^ ]*')
echo -e "${GREEN}✓${NC} 已登入: ${LOGGED_IN_USER}"
echo ""

# 顯示專案資訊
echo -e "${BLUE}📋 專案資訊...${NC}"
railway status | grep -E "Project:|Environment:"
echo ""

# 設定 CORS_ORIGINS 值
CORS_VALUE="*"
FRONTEND_URL="https://tcu-frontend-production.up.railway.app"
API_URL="https://tcu.up.railway.app"

echo -e "${YELLOW}選擇 CORS 設定方式：${NC}"
echo "1. 允許所有來源 (*) - 推薦，最簡單"
echo "2. 明確指定前端 URL - 更安全"
echo ""
read -p "請選擇 (1 或 2，預設 1): " choice

case "$choice" in
    2)
        CORS_VALUE="$FRONTEND_URL,$API_URL"
        echo -e "${GREEN}✓${NC} 將設定為: $CORS_VALUE"
        ;;
    *)
        CORS_VALUE="*"
        echo -e "${GREEN}✓${NC} 將設定為: * (允許所有來源)"
        ;;
esac

echo ""
echo -e "${YELLOW}⚠️  重要提醒：${NC}"
echo "接下來會要求您選擇服務，請選擇 ${YELLOW}API 服務${NC}"
echo "（通常名稱包含 'api'、'backend' 或 URL 為 tcu.up.railway.app）"
echo ""
read -p "按 Enter 繼續..."

# 嘗試設置環境變數
echo ""
echo -e "${BLUE}🔧 設置 CORS_ORIGINS 環境變數...${NC}"
echo ""

# 方法 1：嘗試直接設置（會要求選擇服務）
if railway variables --set "CORS_ORIGINS=$CORS_VALUE" 2>/dev/null; then
    echo ""
    echo -e "${GREEN}✅ CORS_ORIGINS 設定成功！${NC}"
    echo ""
    echo -e "${BLUE}🚀 觸發重新部署...${NC}"
    
    # 觸發重新部署
    railway up --detach 2>/dev/null || echo "（自動部署功能不可用，請在 Dashboard 手動部署）"
    
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ 設定完成！${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "設定值: CORS_ORIGINS=$CORS_VALUE"
    echo ""
    echo "📝 後續步驟："
    echo "1. 等待 API 服務重新部署完成（約 1-3 分鐘）"
    echo "2. 訪問 Railway Dashboard 檢查部署狀態"
    echo "3. 重新整理前端網頁: $FRONTEND_URL"
    echo "4. 檢查是否還有 CORS 錯誤"
    echo ""
else
    echo ""
    echo -e "${YELLOW}⚠️  自動設定失敗（可能需要選擇服務）${NC}"
    echo ""
    echo -e "${BLUE}請手動執行以下步驟：${NC}"
    echo ""
    echo "1. 執行命令選擇 API 服務："
    echo -e "   ${YELLOW}railway service${NC}"
    echo ""
    echo "2. 選擇 API 服務後，執行："
    echo -e "   ${YELLOW}railway variables --set CORS_ORIGINS='$CORS_VALUE'${NC}"
    echo ""
    echo "3. 觸發重新部署："
    echo -e "   ${YELLOW}railway up --detach${NC}"
    echo ""
    echo "或者使用 Railway Dashboard："
    echo "1. 訪問: https://railway.app"
    echo "2. 進入專案 → API 服務 → Variables"
    echo "3. 設定 CORS_ORIGINS=$CORS_VALUE"
    echo ""
fi

