# Frontend 部署問題修復指南

## 🚨 問題描述

Frontend URL (https://tcu-frontend-production.up.railway.app/) 顯示後端 API 響應：
```json
{"message":"慈濟大學招生通路自動開發系統 API","version":"0.1.0","status":"running","docs":"/api/docs"}
```

這表示 Frontend 服務配置錯誤，正在運行後端代碼。

---

## ✅ 立即修復步驟

### 1. 檢查 Railway Frontend 服務配置

登入 Railway Dashboard → 進入專案 → 點擊 **tcu-frontend-production** 服務

### 2. 檢查並修正以下設定

#### ⚙️ Settings → General
```
Service Name: tcu-frontend-production  ✅
Root Directory: frontend               ⚠️ 必須是 "frontend" 不是 "backend"
```

#### 🔨 Settings → Build
```
Builder: Docker                        ✅
Dockerfile Path: Dockerfile            ✅ (相對於 Root Directory)
Watch Paths: [留空或設為 frontend/**]
```

#### 📦 Settings → Deploy
```
Start Command: /start.sh               ✅ (或留空使用 Dockerfile 的 CMD)
```

#### 🌍 Settings → Variables
```
NODE_ENV=production
REACT_APP_API_URL=https://tcu.up.railway.app
PORT=3000
```

**注意：REACT_APP_API_URL 必須指向後端 API 的 URL！**

---

## 🔍 常見錯誤配置

### ❌ 錯誤配置 1: Root Directory 設定錯誤
```
Root Directory: backend  ❌ 錯誤！這會導致運行後端代碼
Root Directory: .        ❌ 錯誤！找不到正確的 Dockerfile
Root Directory: /        ❌ 錯誤！找不到正確的 Dockerfile
```

### ✅ 正確配置
```
Root Directory: frontend  ✅ 正確！
```

### ❌ 錯誤配置 2: Dockerfile Path 設定錯誤
```
Dockerfile Path: backend/Dockerfile   ❌ 錯誤！指向後端
Dockerfile Path: ./Dockerfile         ❌ 可能錯誤
```

### ✅ 正確配置
```
Dockerfile Path: Dockerfile  ✅ 正確！（相對於 Root Directory）
```

---

## 📋 完整檢查清單

完成修正前，請確認：

- [ ] Root Directory 設定為 `frontend`（不是 backend）
- [ ] Dockerfile Path 設定為 `Dockerfile`
- [ ] `REACT_APP_API_URL` 設定為後端 API URL (`https://tcu.up.railway.app`)
- [ ] `NODE_ENV` 設定為 `production`
- [ ] `PORT` 設定為 `3000`
- [ ] 儲存設定後觸發重新部署

---

## 🚀 重新部署

### 方法 1: 透過 Railway Dashboard（推薦）

1. 修改上述設定
2. 點擊 **Deployments** 標籤
3. 點擊右上角 **Deploy** 按鈕
4. 選擇 **Deploy latest commit**
5. 等待部署完成（約 3-5 分鐘）

### 方法 2: 透過 Git Push

```bash
# 在專案目錄執行
cd "/Users/kuoyuming/Desktop/程式開發/auto scraper for oga"

# 推送到 GitHub（會自動觸發 Railway 部署）
git push origin main
```

### 方法 3: 強制重新部署

如果修改設定後沒有自動部署：

1. 進入 Frontend 服務頁面
2. 點擊 **Deployments** 標籤
3. 找到最新的部署
4. 點擊右側的 **⋯** (三個點)
5. 選擇 **Redeploy**

---

## 🔎 部署日誌檢查

部署時請檢查以下日誌：

### Build Logs 應該顯示：
```
Building Docker image from frontend/Dockerfile
Step 1/10 : FROM node:18-alpine AS builder
...
Successfully built React app
Copying to nginx container
```

### Deploy Logs 應該顯示：
```
Starting nginx server
Listening on port 3000
```

### ❌ 如果看到這些，表示配置錯誤：
```
Starting uvicorn...           ← 這是後端！
celery worker starting...     ← 這是 worker！
```

---

## ✅ 驗證部署成功

部署完成後，訪問 https://tcu-frontend-production.up.railway.app/

### 應該看到：
- ✅ React 應用的 UI 介面
- ✅ 慈濟大學招生通路自動開發系統的前端頁面
- ✅ 登入表單或系統首頁

### 不應該看到：
- ❌ JSON 格式的 API 響應
- ❌ `{"message":"...API","version":"0.1.0",...}`

---

## 🆘 如果仍然失敗

### 1. 檢查 frontend/Dockerfile 是否存在

在本地執行：
```bash
ls -la "/Users/kuoyuming/Desktop/程式開發/auto scraper for oga/frontend/Dockerfile"
```

應該看到檔案存在。

### 2. 本地測試 Frontend Docker 構建

```bash
cd "/Users/kuoyuming/Desktop/程式開發/auto scraper for oga/frontend"

# 構建 Docker image
docker build -t test-frontend --build-arg REACT_APP_API_URL=https://tcu.up.railway.app .

# 運行容器
docker run -p 3000:3000 test-frontend

# 訪問 http://localhost:3000 檢查是否正常
```

### 3. 檢查 Railway Service 配置文件

確認 `railway.toml` 中沒有錯誤配置覆蓋 Dashboard 設定。

### 4. 刪除並重新創建 Frontend 服務

如果以上都無法解決：

1. 在 Railway 中刪除 **tcu-frontend-production** 服務
2. 重新創建，嚴格按照配置步驟執行
3. 確保 Root Directory 一開始就設定為 `frontend`

---

## 📞 需要協助？

提供以下資訊：
1. Railway Frontend 服務的 **Build Logs** 截圖
2. Railway Frontend 服務的 **Deploy Logs** 截圖
3. Railway Frontend 服務的 **Settings → General** 截圖（顯示 Root Directory）
4. 訪問 https://tcu-frontend-production.up.railway.app/ 的結果

---

## 🎯 預期結果

修正完成後：

| URL | 顯示內容 |
|-----|---------|
| https://tcu.up.railway.app/ | 後端 API JSON 響應 ✅ |
| https://tcu.up.railway.app/api/docs | API 文檔頁面 ✅ |
| https://tcu-frontend-production.up.railway.app/ | React 前端介面 ✅ |

前端應該能夠連接到後端 API 並正常運作！

