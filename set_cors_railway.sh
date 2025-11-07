#!/bin/bash

# 快速設定 Railway CORS 環境變數
# 使用方式: ./set_cors_railway.sh [service_name]

set -e

echo "🔧 Railway CORS 快速修復工具"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 服務名稱（可以從命令列參數傳入）
SERVICE_NAME="${1:-}"

# 可能的服務名稱列表
POSSIBLE_SERVICES=(
    "tcu-api"
    "api"
    "backend"
    "tcu-backend"
    "production-api"
)

# CORS 設定值
CORS_VALUE="*"

echo "🎯 將設定 CORS_ORIGINS=$CORS_VALUE"
echo ""

# 如果沒有指定服務名稱，嘗試所有可能的名稱
if [ -z "$SERVICE_NAME" ]; then
    echo "🔍 嘗試自動偵測 API 服務..."
    echo ""
    
    for service in "${POSSIBLE_SERVICES[@]}"; do
        echo "嘗試服務: $service"
        if railway variables --service "$service" --set "CORS_ORIGINS=$CORS_VALUE" 2>/dev/null; then
            echo ""
            echo "✅ 成功！在服務 '$service' 設定 CORS_ORIGINS=$CORS_VALUE"
            echo ""
            echo "📝 後續步驟："
            echo "1. 等待 Railway 自動重新部署（約 1-3 分鐘）"
            echo "2. 或手動觸發部署："
            echo "   railway up --detach --service $service"
            echo ""
            echo "3. 重新整理前端網頁測試:"
            echo "   https://tcu-frontend-production.up.railway.app"
            echo ""
            exit 0
        fi
    done
    
    echo ""
    echo "❌ 自動偵測失敗，無法找到 API 服務"
    echo ""
    echo "請手動指定服務名稱："
    echo "  ./set_cors_railway.sh <服務名稱>"
    echo ""
    echo "或使用互動式方式："
    echo "  1. 執行: railway service"
    echo "  2. 選擇 API 服務"
    echo "  3. 執行: railway variables --set \"CORS_ORIGINS=*\""
    echo ""
    exit 1
else
    # 使用指定的服務名稱
    echo "🎯 使用指定的服務: $SERVICE_NAME"
    echo ""
    
    if railway variables --service "$SERVICE_NAME" --set "CORS_ORIGINS=$CORS_VALUE"; then
        echo ""
        echo "✅ 成功！CORS_ORIGINS=$CORS_VALUE"
        echo ""
        echo "📝 後續步驟："
        echo "1. 等待 Railway 自動重新部署（約 1-3 分鐘）"
        echo "2. 重新整理前端網頁: https://tcu-frontend-production.up.railway.app"
        echo ""
    else
        echo ""
        echo "❌ 設定失敗"
        echo ""
        echo "請確認:"
        echo "1. 服務名稱 '$SERVICE_NAME' 是否正確"
        echo "2. 您是否有權限修改此服務"
        echo "3. 已經登入 Railway CLI"
        echo ""
        exit 1
    fi
fi

