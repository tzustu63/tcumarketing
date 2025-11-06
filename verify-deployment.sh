#!/bin/bash

# 部署驗證腳本
# 用於檢查所有服務是否正常運行

SERVER_IP="188.166.228.79"
API_URL="http://${SERVER_IP}:8000"
FRONTEND_URL="http://${SERVER_IP}:3000"

echo "========================================="
echo "慈濟大學招生系統 - 部署驗證"
echo "========================================="
echo ""

# 檢查 API 健康狀態
echo "1. 檢查 API 健康狀態..."
API_HEALTH=$(curl -s ${API_URL}/health)
if echo "$API_HEALTH" | grep -q "healthy"; then
    echo "   ✅ API 健康檢查通過"
else
    echo "   ❌ API 健康檢查失敗"
    exit 1
fi
echo ""

# 檢查 API 統計端點
echo "2. 檢查 API 統計端點..."
API_STATS=$(curl -s ${API_URL}/api/stats)
if echo "$API_STATS" | grep -q "tasks"; then
    echo "   ✅ API 統計端點正常"
else
    echo "   ❌ API 統計端點失敗"
    exit 1
fi
echo ""

# 檢查前端
echo "3. 檢查前端服務..."
FRONTEND_CHECK=$(curl -s ${FRONTEND_URL} | head -20)
if echo "$FRONTEND_CHECK" | grep -q "慈濟大學"; then
    echo "   ✅ 前端服務正常"
else
    echo "   ❌ 前端服務失敗"
    exit 1
fi
echo ""

# 檢查 Docker 容器狀態
echo "4. 檢查 Docker 容器狀態..."
ssh root@${SERVER_IP} "cd /root/tcu-recruitment-system && docker-compose ps" | grep -E "(Up|healthy)" > /dev/null
if [ $? -eq 0 ]; then
    echo "   ✅ 所有容器運行正常"
    echo ""
    echo "   容器狀態："
    ssh root@${SERVER_IP} "cd /root/tcu-recruitment-system && docker-compose ps"
else
    echo "   ❌ 部分容器未運行"
    exit 1
fi
echo ""

echo "========================================="
echo "✅ 部署驗證完成！所有服務正常運行"
echo "========================================="
echo ""
echo "訪問地址："
echo "  前端: ${FRONTEND_URL}"
echo "  API:  ${API_URL}"
echo "  文檔: ${API_URL}/docs"
echo ""
