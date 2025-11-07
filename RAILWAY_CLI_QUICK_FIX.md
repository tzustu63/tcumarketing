# 🚀 Railway CLI 快速修復 CORS（命令列方式）

## 方法 1：一鍵設定（推薦）

在終端執行以下命令：

```bash
cd "/Users/kuoyuming/Desktop/程式開發/auto scraper for oga"

# 顯示所有服務（找到 API 服務名稱）
railway service list

# 設定 CORS_ORIGINS（會要求您選擇服務，請選擇 API 服務）
railway variables --set CORS_ORIGINS="*"

# 觸發重新部署
railway up --detach
```

## 方法 2：使用專案 Token（無需互動）

如果您有專案 Token：

```bash
# 使用您的專案 Token
export RAILWAY_TOKEN=5ff08d2d-64e7-44f0-ab91-d0f28adcf213

# 設定環境變數（需要指定服務名稱）
railway variables --set CORS_ORIGINS="*" --service tcu-api

# 或者允許特定域名
railway variables --set CORS_ORIGINS="https://tcu-frontend-production.up.railway.app,https://tcu.up.railway.app" --service tcu-api
```

## 方法 3：逐步互動式設定

```bash
# 步驟 1：確認登入
railway whoami

# 步驟 2：連結到專案（如果還沒連結）
railway link

# 步驟 3：選擇 API 服務
railway service

# 步驟 4：設定 CORS_ORIGINS
railway variables --set CORS_ORIGINS="*"

# 步驟 5：檢查設定
railway variables

# 步驟 6：觸發重新部署（可選，通常會自動部署）
railway up --detach
```

## 方法 4：使用環境變數指定服務

```bash
# 設定服務名稱環境變數（請替換為您的實際服務名稱）
export RAILWAY_SERVICE="tcu-api"  # 或 "api" 或其他名稱

# 然後設定環境變數
railway variables --set CORS_ORIGINS="*"
```

## 🔍 查找 API 服務名稱

如果不確定 API 服務的名稱，執行：

```bash
# 方法 1：列出所有服務
railway service list

# 方法 2：查看專案狀態
railway status

# 方法 3：進入專案選擇服務
railway service
```

尋找包含以下特徵的服務：
- 名稱包含 "api"、"backend" 或 "tcu-api"
- 環境變數中有 `SERVICE_ROLE=api`
- URL 是 `https://tcu.up.railway.app`

## 📋 完整流程示例

```bash
# 1. 進入專案目錄
cd "/Users/kuoyuming/Desktop/程式開發/auto scraper for oga"

# 2. 確認登入狀態
railway whoami
# 輸出: Logged in as ss248@gms.tcu.edu.tw 👋

# 3. 查看專案資訊
railway status
# 輸出: Project: tcu marketing
#       Environment: production
#       Service: None

# 4. 互動式選擇 API 服務並設定變數
echo "請在下一步選擇 API 服務"
railway service
# （會顯示服務列表，用方向鍵選擇 API 服務，按 Enter 確認）

# 5. 設定 CORS_ORIGINS
railway variables --set CORS_ORIGINS="*"

# 6. 驗證設定
railway variables | grep CORS

# 7. 等待自動部署或手動觸發
# Railway 通常會自動重新部署
# 如果沒有，執行：
railway up --detach
```

## ✅ 驗證設定成功

```bash
# 檢查環境變數是否已設定
railway variables | grep CORS_ORIGINS

# 應該看到：
# CORS_ORIGINS=*
```

## 🔧 故障排除

### 問題 1：`railway variables` 顯示 "No service linked"

**解決方法：**
```bash
# 先選擇服務
railway service
# 然後再設定變數
railway variables --set CORS_ORIGINS="*"
```

### 問題 2：不確定選擇哪個服務

**解決方法：**
查看每個服務的環境變數：

```bash
# 選擇服務後查看變數
railway service
railway variables

# 尋找有 SERVICE_ROLE=api 的服務
```

### 問題 3：設定後沒有自動部署

**解決方法：**
```bash
# 手動觸發部署
railway up --detach

# 或者查看部署日誌
railway logs
```

## 🎯 快速命令參考

```bash
# 一鍵設定（互動式）
railway service && railway variables --set CORS_ORIGINS="*"

# 查看所有環境變數
railway variables

# 查看日誌
railway logs --follow

# 重新部署
railway up --detach

# 連接到服務 shell（進階）
railway shell
```

## 📞 需要協助？

如果以上方法都無法執行，請：

1. 截圖 `railway service list` 的輸出
2. 截圖 `railway status` 的輸出
3. 告訴我遇到的具體錯誤訊息

或者直接使用 Railway Dashboard（更簡單）：
https://railway.app → API 服務 → Variables → 新增 CORS_ORIGINS=*

