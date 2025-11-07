#!/bin/bash

# SSH 連接檢查腳本

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

print_info "========================================="
print_info "SSH 連接檢查工具"
print_info "========================================="
echo ""

# 檢查本地 SSH Key
print_info "檢查本地 SSH Key..."
if [ -f ~/.ssh/id_ed25519.pub ]; then
    print_success "找到 SSH 公鑰: id_ed25519"
    echo ""
    print_info "您的公鑰內容："
    cat ~/.ssh/id_ed25519.pub
    echo ""
elif [ -f ~/.ssh/id_rsa.pub ]; then
    print_success "找到 SSH 公鑰: id_rsa"
    echo ""
    print_info "您的公鑰內容："
    cat ~/.ssh/id_rsa.pub
    echo ""
else
    print_error "未找到 SSH 公鑰"
    echo ""
    print_info "請先執行: ./setup-ssh-key.sh"
    exit 1
fi

# 檢查網路連接
print_info "檢查網路連接..."
if ping -c 1 -W 2 ${DROPLET_IP} &> /dev/null; then
    print_success "網路連接正常"
else
    print_error "無法連接到 Droplet"
    exit 1
fi

# 檢查 SSH 端口
print_info "檢查 SSH 端口..."
if nc -zv -w 2 ${DROPLET_IP} 22 &> /dev/null; then
    print_success "SSH 端口 (22) 開放"
else
    print_error "SSH 端口無法連接"
    exit 1
fi

# 測試 SSH 連接
echo ""
print_info "測試 SSH 連接..."
if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes root@${DROPLET_IP} "echo 'SSH 連接成功！'" &> /dev/null; then
    print_success "✅ SSH 連接成功！"
    echo ""
    print_info "Droplet 資訊："
    ssh root@${DROPLET_IP} "hostname && uptime" 2>/dev/null
    echo ""
    print_success "現在您可以執行部署了！"
    echo ""
    print_info "下一步："
    echo "  1. 執行自動化部署: ./manual-deploy.sh"
    echo "  2. 或參考: QUICK_DEPLOY.md"
    exit 0
else
    print_error "❌ SSH 連接失敗"
    echo ""
    print_warning "可能的原因："
    echo "  1. 公鑰尚未添加到 DigitalOcean Droplet"
    echo "  2. 公鑰格式不正確"
    echo "  3. Droplet 上的 authorized_keys 權限問題"
    echo ""
    print_info "解決方案："
    echo ""
    echo "方法 1: 使用 DigitalOcean 控制台（推薦）"
    echo "  1. 登入 https://cloud.digitalocean.com/"
    echo "  2. 進入 Droplet → Settings → Security"
    echo "  3. 點擊 'Add SSH Key'"
    echo "  4. 貼上上面的公鑰內容"
    echo "  5. 點擊 'Add SSH Key'"
    echo ""
    echo "方法 2: 使用網頁終端機"
    echo "  1. 登入 DigitalOcean 控制台"
    echo "  2. 進入 Droplet → Access → Launch Droplet Console"
    echo "  3. 執行以下命令："
    echo ""
    if [ -f ~/.ssh/id_ed25519.pub ]; then
        PUB_KEY=$(cat ~/.ssh/id_ed25519.pub)
    else
        PUB_KEY=$(cat ~/.ssh/id_rsa.pub)
    fi
    echo "     mkdir -p ~/.ssh"
    echo "     chmod 700 ~/.ssh"
    echo "     echo '$PUB_KEY' >> ~/.ssh/authorized_keys"
    echo "     chmod 600 ~/.ssh/authorized_keys"
    echo ""
    print_info "添加公鑰後，再次執行此腳本檢查："
    echo "  ./check-ssh-connection.sh"
    exit 1
fi

