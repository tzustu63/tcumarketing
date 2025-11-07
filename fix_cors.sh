#!/bin/bash

# 修復 Railway CORS 問題腳本

echo "🔧 修復 Railway API CORS 設定..."
echo ""

# 前端 URL
FRONTEND_URL="https://tcu-frontend-production.up.railway.app"
API_URL="https://tcu.up.railway.app"

echo "前端 URL: $FRONTEND_URL"
echo "API URL: $API_URL"
echo ""

# 設定 CORS_ORIGINS（允許所有來源）
echo "設定 CORS_ORIGINS 為允許所有來源..."

# 注意：這需要先連結到 API 服務
# railway link 然後選擇專案和 API 服務

echo ""
echo "請在 Railway Dashboard 執行以下操作："
echo ""
echo "1. 登入 Railway Dashboard: https://railway.app"
echo "2. 進入您的專案: tcu marketing"
echo "3. 點擊 API 服務 (tcu-api)"
echo "4. 點擊 Variables 標籤"
echo "5. 找到或新增 CORS_ORIGINS 變數"
echo "6. 設定值為："
echo ""
echo "   CORS_ORIGINS=*"
echo ""
echo "   或者明確指定："
echo ""
echo "   CORS_ORIGINS=$FRONTEND_URL,$API_URL"
echo ""
echo "7. 儲存後 Railway 會自動重新部署"
echo ""
echo "等待 2-3 分鐘後重新載入前端網頁測試"
echo ""

