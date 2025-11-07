#!/bin/bash

# 檢查 Dockerfile 配置腳本
# 用於驗證 Railway 應該使用哪個 Dockerfile

echo "🔍 檢查專案中的 Dockerfile..."
echo ""

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 檢查根目錄的 Dockerfiles
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📁 根目錄的 Dockerfiles："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "Dockerfile.api" ]; then
    echo -e "${GREEN}✓${NC} Dockerfile.api ${YELLOW}(後端 API - Python/FastAPI)${NC}"
    echo "  用途：構建後端服務"
    echo "  第一行：$(head -n 1 Dockerfile.api)"
    echo ""
fi

if [ -f "Dockerfile.frontend" ]; then
    echo -e "${GREEN}✓${NC} Dockerfile.frontend ${BLUE}(前端 - React/Nginx)${NC}"
    echo "  用途：構建前端服務"
    echo "  第一行：$(head -n 1 Dockerfile.frontend)"
    echo ""
fi

# 檢查 backend 目錄
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📁 backend/Dockerfile："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "backend/Dockerfile" ]; then
    echo -e "${GREEN}✓${NC} backend/Dockerfile ${YELLOW}(後端 API - Python/FastAPI)${NC}"
    echo "  用途：構建後端服務（從 backend 目錄）"
    echo "  第一行：$(head -n 1 backend/Dockerfile)"
    echo ""
fi

# 檢查 frontend 目錄
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📁 frontend/Dockerfile："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "frontend/Dockerfile" ]; then
    echo -e "${GREEN}✓${NC} frontend/Dockerfile ${BLUE}(前端 - React/Nginx)${NC}"
    echo "  用途：構建前端服務（從 frontend 目錄）"
    echo "  第一行：$(head -n 1 frontend/Dockerfile)"
    echo ""
fi

# Railway 配置建議
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Railway 配置建議："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo -e "${YELLOW}方案 1：使用根目錄的 Dockerfile（推薦）${NC}"
echo "  Root Directory: [留空] 或 '.'"
echo "  Dockerfile Path: Dockerfile.frontend"
echo ""

echo -e "${BLUE}方案 2：使用 frontend 子目錄的 Dockerfile${NC}"
echo "  Root Directory: frontend"
echo "  Dockerfile Path: Dockerfile"
echo ""

# 檢測哪些文件包含 Python（後端）
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Dockerfile 內容檢測："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f "Dockerfile.api" ]; then
    if grep -q "FROM python" Dockerfile.api; then
        echo -e "${YELLOW}Dockerfile.api${NC} → ${RED}Python/後端${NC}"
    fi
fi

if [ -f "Dockerfile.frontend" ]; then
    if grep -q "FROM node" Dockerfile.frontend; then
        echo -e "${BLUE}Dockerfile.frontend${NC} → ${GREEN}Node.js/前端${NC}"
    fi
fi

if [ -f "backend/Dockerfile" ]; then
    if grep -q "FROM python" backend/Dockerfile; then
        echo -e "${YELLOW}backend/Dockerfile${NC} → ${RED}Python/後端${NC}"
    fi
fi

if [ -f "frontend/Dockerfile" ]; then
    if grep -q "FROM node" frontend/Dockerfile; then
        echo -e "${BLUE}frontend/Dockerfile${NC} → ${GREEN}Node.js/前端${NC}"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚠️  重要提醒："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "如果 Railway Frontend 服務顯示 API JSON 響應，"
echo "表示它正在使用 ${RED}Python/後端${NC} 的 Dockerfile！"
echo ""
echo "請確認 Railway 配置："
echo "  ❌ 不能是：backend/Dockerfile"
echo "  ❌ 不能是：Dockerfile.api"
echo "  ✅ 應該是：Dockerfile.frontend"
echo "  ✅ 或者是：frontend/Dockerfile (配合 Root Directory: frontend)"
echo ""

# 測試 Dockerfile.frontend 是否在 Git 中
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 Git 狀態檢查："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if git ls-tree HEAD Dockerfile.frontend &>/dev/null; then
    echo -e "${GREEN}✓${NC} Dockerfile.frontend 已提交到 Git"
else
    echo -e "${RED}✗${NC} Dockerfile.frontend 未找到在 Git 中"
    echo "  請執行："
    echo "  git add Dockerfile.frontend"
    echo "  git commit -m 'Add frontend Dockerfile'"
    echo "  git push origin main"
fi

if git ls-tree HEAD frontend/Dockerfile &>/dev/null; then
    echo -e "${GREEN}✓${NC} frontend/Dockerfile 已提交到 Git"
else
    echo -e "${RED}✗${NC} frontend/Dockerfile 未找到在 Git 中"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 檢查完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

