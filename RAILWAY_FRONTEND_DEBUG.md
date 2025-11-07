# 🔍 Railway Frontend 問題診斷與修復

## 當前問題

訪問 https://tcu-frontend-production.up.railway.app/ 仍然顯示：
```json
{"message":"慈濟大學招生通路自動開發系統 API","version":"0.1.0","status":"running","docs":"/api/docs"}
```

這表示 **Frontend 服務仍在運行後端代碼**。

---

## 🎯 核心問題分析

Railway 正在使用**錯誤的 Dockerfile** 構建 Frontend 服務。

### 檔案結構說明

您的專案有以下 Dockerfile：

```
專案根目錄/
├── Dockerfile.api          ← 後端 API（Python/FastAPI）
├── Dockerfile.frontend     ← 前端（React/Nginx）從根目錄構建
├── backend/
│   └── Dockerfile          ← 後端（Python/FastAPI）從 backend 目錄構建
└── frontend/
    └── Dockerfile          ← 前端（React/Nginx）從 frontend 目錄構建
```

### Dockerfile 內容差異

**❌ 後端 Dockerfile (Dockerfile.api 或 backend/Dockerfile):**
```dockerfile
FROM python:3.11-slim
RUN apt-get install chromium
COPY backend/requirements.txt .
CMD ["/app/start.sh"]  # 啟動 FastAPI
```

**✅ 前端 Dockerfile (Dockerfile.frontend 或 frontend/Dockerfile):**
```dockerfile
FROM node:18-alpine AS builder
RUN npm install
RUN npm run build
FROM nginx:alpine
CMD ["/start.sh"]  # 啟動 Nginx
```

---

## ✅ 修復步驟（請跟著做）

### 第 1 步：登入 Railway Dashboard

1. 開啟瀏覽器
2. 訪問：https://railway.app/
3. 登入帳號：ss248@gms.tcu.edu.tw

### 第 2 步：進入專案

1. 在 Dashboard 中找到 **"tcu marketing"** 專案
2. 點擊進入

### 第 3 步：找到 Frontend 服務

在專案中應該會看到多個服務：
- tcu-api 或類似名稱
- tcu-frontend-production ← **點擊這個**
- PostgreSQL
- Redis
- 其他服務...

**點擊 `tcu-frontend-production` 服務**

### 第 4 步：檢查並修改配置

#### 📍 檢查點 A：Settings → General

點擊左側的 **"Settings"** 標籤，然後查看 **General** 區塊：

```
當前配置可能是 ❌：
┌─────────────────────────────────────┐
│ Service Name: tcu-frontend-production│
│ Root Directory: backend             │ ← 錯誤！
│ Watch Paths: backend/**             │ ← 錯誤！
└─────────────────────────────────────┘

應該改成 ✅：
┌─────────────────────────────────────┐
│ Service Name: tcu-frontend-production│
│ Root Directory: [留空]              │ ← 留空或填 "."
│ Watch Paths: frontend/**            │
└─────────────────────────────────────┘
```

**如何修改：**
1. 找到 **"Root Directory"** 欄位
2. 如果顯示 `backend`，**清空它** 或改成 `.`
3. 找到 **"Watch Paths"** 欄位
4. 改成 `frontend/**`
5. 點擊 **"Save"** 或 **"Update"**

#### 📍 檢查點 B：Settings → Build

在同一個 Settings 頁面，往下滾動找到 **Build** 區塊：

```
當前配置可能是 ❌：
┌─────────────────────────────────────┐
│ Builder: Docker                     │ ← 正確
│ Dockerfile Path: backend/Dockerfile │ ← 錯誤！
│ Docker Build Args: [none]           │
└─────────────────────────────────────┘

應該改成 ✅：
┌─────────────────────────────────────┐
│ Builder: Docker                     │ ← 正確
│ Dockerfile Path: Dockerfile.frontend│ ← 改這個！
│ Docker Build Args:                  │
│   REACT_APP_API_URL=https://tcu.up.railway.app │
└─────────────────────────────────────┘
```

**如何修改：**
1. 找到 **"Dockerfile Path"** 欄位
2. 改成：`Dockerfile.frontend`
3. 找到 **"Build Args"** 區域
4. 新增：
   - Key: `REACT_APP_API_URL`
   - Value: `https://tcu.up.railway.app`
5. 點擊 **"Save"** 或 **"Update"**

#### 📍 檢查點 C：Settings → Variables

在左側找到 **"Variables"** 標籤並點擊：

```
應該有以下環境變數 ✅：
┌──────────────────────────────────────────┐
│ NODE_ENV = production                    │
│ REACT_APP_API_URL = https://tcu.up.railway.app │
│ PORT = 3000                              │
└──────────────────────────────────────────┘

如果缺少，請新增：
```

**如何新增：**
1. 點擊 **"+ New Variable"** 按鈕
2. 添加每個變數的 Name 和 Value
3. 確認所有三個變數都存在

### 第 5 步：觸發重新部署

修改完所有配置後：

**方法 1：自動觸發（如果啟用了自動部署）**
- 修改配置後 Railway 會自動重新部署

**方法 2：手動觸發**
1. 點擊左側的 **"Deployments"** 標籤
2. 點擊右上角的 **"Deploy"** 按鈕
3. 或者找到最新的部署，點擊 **"⋯"**（三個點），選擇 **"Redeploy"**

### 第 6 步：觀察部署日誌

部署開始後，點擊最新的部署查看日誌：

#### ✅ 正確的 Build Logs（Frontend）：

```log
Building from /Dockerfile.frontend
#1 [internal] load build definition from Dockerfile.frontend
Step 1/10 : FROM node:18-alpine AS builder
 ---> Pulling from library/node
Step 2/10 : WORKDIR /app
 ---> Running in abc123
Step 5/10 : RUN npm install
 ---> Running in def456
added 1234 packages
Step 7/10 : RUN npm run build
Creating an optimized production build...
Compiled successfully!
Step 9/10 : FROM nginx:alpine
 ---> Pulling from library/nginx
Successfully built abc123def456
```

**關鍵詞：** `node:18-alpine`, `npm install`, `npm run build`, `nginx:alpine`

#### ❌ 錯誤的 Build Logs（Backend）：

```log
Building from /backend/Dockerfile
Step 1/8 : FROM python:3.11-slim
 ---> Pulling from library/python
Step 3/8 : RUN apt-get update && apt-get install chromium
Step 5/8 : COPY backend/requirements.txt .
Step 6/8 : RUN pip install --no-cache-dir -r requirements.txt
Installing uvicorn...
Installing fastapi...
```

**關鍵詞：** `python:3.11`, `pip install`, `requirements.txt`, `uvicorn`

**⚠️ 如果看到錯誤的日誌，表示配置還沒生效，請重新檢查第 4 步的配置！**

### 第 7 步：驗證部署成功

部署完成後（狀態顯示綠色 ✓）：

1. 訪問：https://tcu-frontend-production.up.railway.app/
2. **應該看到：**
   - ✅ React 網頁界面
   - ✅ 登入頁面或儀表板
   - ✅ 慈濟大學招生系統的 UI

3. **不應該看到：**
   - ❌ JSON 格式：`{"message":"...API"...}`
   - ❌ 404 錯誤
   - ❌ Nginx 預設頁面

---

## 🔧 進階診斷

### 如果修改後仍然失敗

#### 診斷 1：檢查部署使用的 Dockerfile

在 Deployment 的 Build Logs 中，第一行應該顯示：
```
Building from /Dockerfile.frontend
```

如果顯示其他路徑（如 `/backend/Dockerfile`），表示配置沒有生效。

#### 診斷 2：檢查服務是否有多個 Git Repo

1. 在服務的 Settings → General 中
2. 確認 **"Source Repo"** 是正確的
3. 確認 **"Branch"** 是 `main`

#### 診斷 3：清除快取重新構建

1. 進入 Deployments
2. 點擊最新部署的 **"⋯"** 菜單
3. 選擇 **"Remove Build Cache"**
4. 重新部署

#### 診斷 4：檢查 Dockerfile.frontend 是否存在

在本地執行：
```bash
ls -la "/Users/kuoyuming/Desktop/程式開發/auto scraper for oga/Dockerfile.frontend"
```

如果檔案存在，確認 Git 已經推送：
```bash
git log --oneline -1
git ls-tree main Dockerfile.frontend
```

---

## 🆘 最後手段：刪除並重建服務

如果以上都無法解決：

### 步驟 1：記錄環境變數

在刪除前，先複製所有環境變數到記事本。

### 步驟 2：刪除 Frontend 服務

1. 進入 `tcu-frontend-production` 服務
2. Settings → Danger → **Delete Service**
3. 確認刪除

### 步驟 3：重新創建 Frontend 服務

1. 在專案中點擊 **"+ New"**
2. 選擇 **"GitHub Repo"**
3. 選擇您的 repository：`tzustu63/tcumarketing`
4. **立即設定（不要等部署開始）：**

   **Settings → General:**
   - Service Name: `tcu-frontend`
   - Root Directory: **留空**

   **Settings → Build:**
   - Builder: `Docker`
   - Dockerfile Path: `Dockerfile.frontend`
   - Build Args: `REACT_APP_API_URL=https://tcu.up.railway.app`

   **Settings → Variables:**
   ```
   NODE_ENV=production
   REACT_APP_API_URL=https://tcu.up.railway.app
   PORT=3000
   ```

5. 觸發部署
6. 等待完成

---

## 📸 需要截圖協助

如果仍然無法解決，請提供以下截圖：

1. **Settings → General** 的完整頁面（包含 Service Name、Root Directory）
2. **Settings → Build** 的完整頁面（包含 Builder、Dockerfile Path）
3. **Variables** 頁面的所有環境變數
4. **最新部署的 Build Logs**（前 50 行）
5. **最新部署的 Deploy Logs**（前 50 行）

---

## ✅ 成功檢查清單

部署成功後，確認：

- [ ] Build Logs 中出現 `FROM node:18-alpine`
- [ ] Build Logs 中出現 `npm run build`
- [ ] Build Logs 中出現 `FROM nginx:alpine`
- [ ] Deploy Logs 中出現 `nginx` 相關訊息
- [ ] 訪問 https://tcu-frontend-production.up.railway.app/ 看到網頁界面
- [ ] 不再看到 JSON API 響應

---

## 🎯 快速參考卡

```
┌────────────────────────────────────────┐
│ Railway Frontend 正確配置速查表         │
├────────────────────────────────────────┤
│ Root Directory: [空白]                 │
│ Dockerfile Path: Dockerfile.frontend   │
│ Build Arg: REACT_APP_API_URL=...       │
│ 環境變數:                              │
│   - NODE_ENV=production                │
│   - REACT_APP_API_URL=https://tcu...   │
│   - PORT=3000                          │
│                                        │
│ 驗證方式:                              │
│   Build Logs 必須包含 "node" 和 "npm"  │
│   不能包含 "python" 或 "pip"           │
└────────────────────────────────────────┘
```

請按照上述步驟操作，並告訴我進展如何！🚀

