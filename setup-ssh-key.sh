#!/bin/bash

# SSH Key 配置腳本
# 用於修復 DigitalOcean 連接問題

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
print_info "SSH Key 配置工具"
print_info "========================================="
echo ""

# 檢查是否已有 SSH Key
KEY_FILE=""
PUB_KEY_FILE=""

if [ -f ~/.ssh/id_ed25519 ]; then
    KEY_FILE=~/.ssh/id_ed25519
    PUB_KEY_FILE=~/.ssh/id_ed25519.pub
    print_info "發現現有的 SSH Key: id_ed25519"
elif [ -f ~/.ssh/id_rsa ]; then
    KEY_FILE=~/.ssh/id_rsa
    PUB_KEY_FILE=~/.ssh/id_rsa.pub
    print_info "發現現有的 SSH Key: id_rsa"
else
    print_warning "未找到 SSH Key，將生成新的..."
    echo ""
    read -p "請輸入您的 Email（用於標識 Key）: " EMAIL
    
    if [ -z "$EMAIL" ]; then
        EMAIL="digitalocean-deploy@$(hostname)"
    fi
    
    print_info "生成新的 SSH Key..."
    ssh-keygen -t ed25519 -C "$EMAIL" -f ~/.ssh/id_ed25519 -N "" || {
        print_warning "ed25519 不支持，使用 RSA..."
        ssh-keygen -t rsa -b 4096 -C "$EMAIL" -f ~/.ssh/id_rsa -N ""
        KEY_FILE=~/.ssh/id_rsa
        PUB_KEY_FILE=~/.ssh/id_rsa.pub
    }
    
    if [ -z "$KEY_FILE" ]; then
        KEY_FILE=~/.ssh/id_ed25519
        PUB_KEY_FILE=~/.ssh/id_ed25519.pub
    fi
    
    print_success "SSH Key 生成完成！"
fi

# 設置正確的權限
chmod 700 ~/.ssh
chmod 600 "$KEY_FILE"
chmod 644 "$PUB_KEY_FILE"

# 顯示公鑰
echo ""
print_success "========================================="
print_success "您的 SSH 公鑰："
print_success "========================================="
echo ""
cat "$PUB_KEY_FILE"
echo ""
print_success "========================================="
echo ""

# 提供添加公鑰的說明
print_info "請按照以下步驟將公鑰添加到 DigitalOcean："
echo ""
echo "方法 1: 使用 DigitalOcean 控制台（推薦）"
echo "  1. 登入 https://cloud.digitalocean.com/"
echo "  2. 進入 Droplet 頁面"
echo "  3. 點擊 'Settings' → 'Security'"
echo "  4. 在 'SSH Keys' 部分，點擊 'Add SSH Key'"
echo "  5. 複製上面的公鑰內容並貼上"
echo "  6. 點擊 'Add SSH Key'"
echo ""
echo "方法 2: 使用網頁終端機"
echo "  1. 登入 DigitalOcean 控制台"
echo "  2. 進入 Droplet → 'Access' → 'Launch Droplet Console'"
echo "  3. 執行以下命令："
echo ""
echo "     mkdir -p ~/.ssh"
echo "     chmod 700 ~/.ssh"
echo "     echo '$(cat $PUB_KEY_FILE)' >> ~/.ssh/authorized_keys"
echo "     chmod 600 ~/.ssh/authorized_keys"
echo ""

# 詢問是否要測試連接
echo ""
read -p "公鑰添加完成後，是否要測試連接？(y/n): " TEST_CONN

if [ "$TEST_CONN" = "y" ] || [ "$TEST_CONN" = "Y" ]; then
    echo ""
    print_info "測試 SSH 連接..."
    
    # 等待用戶添加公鑰
    read -p "請先完成公鑰添加，然後按 Enter 繼續..."
    
    if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@${DROPLET_IP} "echo 'SSH 連接成功！'" 2>/dev/null; then
        print_success "✅ SSH 連接成功！"
        echo ""
        print_info "現在您可以使用以下命令連接："
        echo "  ssh root@${DROPLET_IP}"
        echo ""
        print_info "或者使用自動化部署腳本："
        echo "  ./manual-deploy.sh"
    else
        print_error "❌ SSH 連接失敗"
        echo ""
        print_warning "可能的原因："
        echo "  1. 公鑰尚未添加到 Droplet"
        echo "  2. 需要等待幾秒讓配置生效"
        echo "  3. Droplet 的 SSH 配置問題"
        echo ""
        print_info "請檢查："
        echo "  - 確認公鑰已正確添加到 DigitalOcean"
        echo "  - 嘗試使用 DigitalOcean 網頁終端機手動添加"
    fi
fi

# 創建 SSH 配置文件
echo ""
read -p "是否要創建 SSH 配置文件以便更容易連接？(y/n): " CREATE_CONFIG

if [ "$CREATE_CONFIG" = "y" ] || [ "$CREATE_CONFIG" = "Y" ]; then
    if [ ! -f ~/.ssh/config ]; then
        touch ~/.ssh/config
        chmod 600 ~/.ssh/config
    fi
    
    if ! grep -q "Host digitalocean" ~/.ssh/config; then
        cat >> ~/.ssh/config << EOF

Host digitalocean
    HostName ${DROPLET_IP}
    User root
    IdentityFile ${KEY_FILE}
    ServerAliveInterval 60
    ServerAliveCountMax 3
EOF
        print_success "SSH 配置文件已創建！"
        echo ""
        print_info "現在您可以使用簡短命令連接："
        echo "  ssh digitalocean"
    else
        print_info "SSH 配置已存在"
    fi
fi

echo ""
print_success "========================================="
print_success "配置完成！"
print_success "========================================="
echo ""

