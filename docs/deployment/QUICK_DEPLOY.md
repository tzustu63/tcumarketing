# 快速部署指南（最簡單方式）

## 🚀 一鍵部署到 DigitalOcean

### 前置準備

1. **專案文件已準備好** ✅
   - 位置：`/tmp/recruitment-system.tar.gz` (330KB)
   - 自動化腳本：`deploy-on-droplet.sh`

2. **連接到 Droplet**
   - IP: 159.223.69.74
   - 使用 DigitalOcean 控制台網頁終端機（最簡單）

---

## 部署步驟（3 步完成）

### 步驟 1: 上傳文件到 Droplet

#### 方法 A: 使用 DigitalOcean 控制台（推薦）

1. 登入 https://cloud.digitalocean.com/
2. 進入 Droplet 頁面
3. 點擊 "Access" → "Launch Droplet Console"
4. 在網頁終端機執行：

```bash
# 創建應用目錄
mkdir -p /opt/apps
cd /opt/apps
```

5. 使用文件上傳功能：
   - 在網頁終端機中，點擊 "Upload" 或使用 `rz` 命令
   - 上傳 `/tmp/recruitment-system.tar.gz`
   - 上傳 `deploy-on-droplet.sh`

#### 方法 B: 使用 SCP（如果有 SSH 訪問）

在**本地電腦**執行：

```bash
# 上傳專案文件
scp /tmp/recruitment-system.tar.gz root@159.223.69.74:/tmp/

# 上傳自動化腳本
scp deploy-on-droplet.sh root@159.223.69.74:/tmp/
```

---

### 步驟 2: 解壓文件

在 **Droplet** 上執行：

```bash
# 進入應用目錄
cd /opt/apps

# 解壓專案文件
tar -xzf /tmp/recruitment-system.tar.gz
rm /tmp/recruitment-system.tar.gz

# 移動自動化腳本
mv /tmp/deploy-on-droplet.sh .
chmod +x deploy-on-droplet.sh
```

---

### 步驟 3: 執行自動化部署

在 **Droplet** 上執行：

```bash
# 執行自動化部署腳本
./deploy-on-droplet.sh
```

**腳本會自動完成：**
- ✅ 創建必要目錄
- ✅ 配置環境變數（自動生成資料庫密碼）
- ✅ 停止現有服務
- ✅ 建置 Docker 映像
- ✅ 啟動所有服務
- ✅ 等待資料庫就緒
- ✅ 執行資料庫遷移
- ✅ 檢查服務狀態
- ✅ 測試 API

**預計時間：** 5-10 分鐘

---

## 完成！

部署完成後，您會看到：

```
=========================================
部署完成！
=========================================

訪問地址:
  前端: http://159.223.69.74:3000
  API: http://159.223.69.74:8000
  API 文件: http://159.223.69.74:8000/docs
```

---

## 驗證部署

### 檢查服務狀態

```bash
cd /opt/apps
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

### 測試 API

```bash
# 在 Droplet 上
curl http://localhost:8000/health

# 從本地電腦
curl http://159.223.69.74:8000/health
```

### 訪問應用

- **前端**: http://159.223.69.74:3000
- **API**: http://159.223.69.74:8000
- **API 文件**: http://159.223.69.74:8000/docs

---

## 重要提醒

1. **記住資料庫密碼**
   - 部署腳本會顯示資料庫密碼
   - 請保存此密碼以備後用

2. **設定 Google API Key（可選）**
   ```bash
   cd /opt/apps
   nano .env
   # 編輯 GOOGLE_API_KEY 和 GOOGLE_CSE_ID
   # 然後重啟服務
   docker compose -f docker-compose.yml -f docker-compose.prod.yml restart
   ```

3. **配置防火牆（如果尚未配置）**
   ```bash
   apt install -y ufw
   ufw allow 22/tcp
   ufw allow 80/tcp
   ufw allow 443/tcp
   ufw allow 8000/tcp
   ufw allow 3000/tcp
   echo "y" | ufw enable
   ```

---

## 故障排除

如果遇到問題，請參考：
- `DIGITALOCEAN_TROUBLESHOOTING.md` - 詳細故障排除指南
- `DEPLOY_MANUAL_STEPS.md` - 完整手動部署步驟

### 快速修復命令

```bash
cd /opt/apps

# 查看日誌
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# 重啟服務
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart

# 重新部署
./deploy-on-droplet.sh
```

---

**就是這麼簡單！** 🎉

