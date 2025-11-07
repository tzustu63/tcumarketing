# 🔧 Railway CORS 錯誤修復指南

## 🎉 好消息！

您的前端服務已經成功部署！現在遇到的是 **CORS（跨域資源共享）** 問題，這很容易修復。

---

## 📋 問題說明

### 錯誤訊息：
```
Access to XMLHttpRequest at 'https://tcu.up.railway.app/api/tasks' 
from origin 'https://tcu-frontend-production.up.railway.app' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present
```

### 原因：
- 前端 URL：`https://tcu-frontend-production.up.railway.app`
- 後端 API URL：`https://tcu.up.railway.app`
- 瀏覽器的安全政策阻止前端訪問後端（不同域名）
- 需要後端明確允許前端域名訪問

---

## ✅ 修復步驟（3 分鐘搞定）

### 步驟 1：登入 Railway Dashboard

1. 開啟瀏覽器
2. 訪問：https://railway.app
3. 登入帳號：`ss248@gms.tcu.edu.tw`

### 步驟 2：進入 API 服務

1. 在 Dashboard 中找到 **"tcu marketing"** 專案
2. 點擊進入專案
3. 找到 **API 服務**（可能名稱是 `tcu-api`、`api`、或顯示 `https://tcu.up.railway.app`）
4. 點擊該服務

### 步驟 3：修改 CORS 環境變數

#### A. 檢查是否已有 CORS_ORIGINS 變數

1. 點擊左側的 **"Variables"** 標籤
2. 查看是否有 `CORS_ORIGINS` 變數

#### B. 如果已有該變數：

點擊 `CORS_ORIGINS` 旁邊的編輯按鈕，修改值為：

**選項 1：允許所有來源（最簡單，推薦用於開發/測試）**
```
*
```

**選項 2：明確指定允許的域名（生產環境推薦）**
```
https://tcu-frontend-production.up.railway.app,https://tcu.up.railway.app
```

點擊 **Save** 或按 Enter 儲存。

#### C. 如果沒有該變數：

1. 點擊右上角的 **"+ New Variable"** 按鈕
2. 在彈出的對話框中：
   - **Name (變數名)**: `CORS_ORIGINS`
   - **Value (變數值)**: `*`
3. 點擊 **Add** 或 **Save**

### 步驟 4：等待自動重新部署

1. Railway 檢測到環境變數變更後會自動重新部署
2. 點擊左側的 **"Deployments"** 標籤查看進度
3. 等待部署完成（顯示綠色 ✓，約 1-3 分鐘）

### 步驟 5：驗證修復成功

1. 回到前端網頁：https://tcu-frontend-production.up.railway.app
2. 重新整理頁面（Ctrl+F5 或 Cmd+Shift+R 強制重新載入）
3. 檢查是否能正常載入資料

---

## 🔍 驗證方式

### ✅ 修復成功的跡象：

1. 前端頁面能正常顯示資料
2. 瀏覽器控制台（F12）沒有 CORS 錯誤
3. 網路請求（Network 標籤）顯示 API 請求成功（狀態碼 200）

### ❌ 仍然失敗的跡象：

1. 控制台仍顯示 CORS 錯誤
2. 顯示「無法連接到伺服器」

---

## 🔧 進階設定

### 配置選項說明

#### 選項 1：允許所有來源 `*`
```bash
CORS_ORIGINS=*
```

**優點：**
- 設定簡單，一步搞定
- 適合開發、測試環境
- 未來更改前端域名不需要更新

**缺點：**
- 安全性較低（任何網站都能訪問您的 API）
- 不建議用於生產環境（如果 API 有敏感資料）

#### 選項 2：明確指定域名（推薦生產環境）
```bash
CORS_ORIGINS=https://tcu-frontend-production.up.railway.app,https://tcu.up.railway.app
```

**優點：**
- 安全性高，只允許指定的域名
- 符合生產環境最佳實踐

**缺點：**
- 需要明確知道所有前端域名
- 更改域名時需要更新設定

#### 選項 3：使用萬用字元（次級域名）
```bash
CORS_ORIGINS=https://*.up.railway.app
```

**注意：** 後端程式碼需要支援萬用字元，目前您的配置不支援這種格式。

---

## 🚨 常見問題排除

### Q1: 修改變數後仍然看到 CORS 錯誤

**A:** 請確認：
1. API 服務已經重新部署完成（Deployments 標籤顯示綠色 ✓）
2. 瀏覽器已經強制重新整理（Ctrl+F5 或 Cmd+Shift+R）
3. 清除瀏覽器快取或使用無痕模式測試
4. 檢查 API 服務的 Deploy Logs 確認沒有啟動錯誤

### Q2: 不確定 API 服務是哪個

**A:** 在專案中查找：
1. 有設定 `SERVICE_ROLE=api` 環境變數的服務
2. 或者 URL 顯示為 `https://tcu.up.railway.app` 的服務
3. 或者名稱包含 `api`、`backend` 的服務

### Q3: 變數設定後 Railway 沒有自動部署

**A:** 手動觸發部署：
1. 進入 API 服務
2. 點擊 **Deployments** 標籤
3. 點擊右上角的 **Deploy** 按鈕
4. 選擇 **Deploy latest commit**

### Q4: API 部署成功但前端仍無法連接

**A:** 檢查前端的 API URL 設定：
1. 進入 Frontend 服務
2. 點擊 **Variables** 標籤
3. 確認 `REACT_APP_API_URL` 的值為：`https://tcu.up.railway.app`
4. 如果不正確，修改後重新部署 Frontend

---

## 📊 環境變數完整檢查清單

### API 服務應該有的環境變數：

```bash
# 資料庫
DATABASE_URL=postgresql://... (自動注入)

# Redis
REDIS_URL=redis://... (自動注入)

# 服務角色
SERVICE_ROLE=api

# CORS 設定（重要！）
CORS_ORIGINS=*

# 其他設定
PORT=8000
UVICORN_RELOAD=false
API_HOST=0.0.0.0
LOG_LEVEL=INFO
GOOGLE_API_KEY=你的金鑰
GOOGLE_CSE_ID=你的CSE_ID
```

### Frontend 服務應該有的環境變數：

```bash
# Node 環境
NODE_ENV=production

# API 連接（重要！）
REACT_APP_API_URL=https://tcu.up.railway.app

# 端口
PORT=3000
```

---

## 🧪 測試 API CORS 設定

### 方法 1：使用瀏覽器控制台

1. 打開前端網頁：https://tcu-frontend-production.up.railway.app
2. 按 F12 打開開發者工具
3. 切換到 **Console** 標籤
4. 輸入以下命令：

```javascript
fetch('https://tcu.up.railway.app/health')
  .then(res => res.json())
  .then(data => console.log('✅ CORS 正常:', data))
  .catch(err => console.error('❌ CORS 錯誤:', err))
```

如果顯示 `✅ CORS 正常: {...}`，表示修復成功！

### 方法 2：使用 curl 測試 CORS 標頭

在本地終端執行：

```bash
curl -I \
  -H "Origin: https://tcu-frontend-production.up.railway.app" \
  -H "Access-Control-Request-Method: GET" \
  -X OPTIONS \
  https://tcu.up.railway.app/api/tasks
```

**成功的響應應該包含：**
```
access-control-allow-origin: *
或
access-control-allow-origin: https://tcu-frontend-production.up.railway.app
```

---

## 📝 修復記錄模板

完成修復後，記錄以下資訊供日後參考：

```
日期：2025-11-07
問題：CORS 錯誤阻止前端訪問後端 API
修復方式：在 Railway API 服務設定 CORS_ORIGINS=*
修復時間：約 3 分鐘
結果：✅ 成功 / ❌ 失敗
備註：
```

---

## 🎯 快速參考卡

```
┌─────────────────────────────────────────┐
│ CORS 修復速查表                          │
├─────────────────────────────────────────┤
│ 1. Railway Dashboard → API 服務         │
│ 2. Variables → 找到/新增 CORS_ORIGINS   │
│ 3. 設定值為: *                          │
│ 4. 等待自動重新部署 (1-3 分鐘)          │
│ 5. 重新整理前端網頁測試                 │
│                                         │
│ 驗證：瀏覽器 F12 控制台無 CORS 錯誤     │
└─────────────────────────────────────────┘
```

---

## ✅ 成功檢查清單

修復完成後，確認：

- [ ] API 服務有 `CORS_ORIGINS` 環境變數
- [ ] `CORS_ORIGINS` 值為 `*` 或包含前端 URL
- [ ] API 服務已重新部署完成
- [ ] 前端頁面重新整理後無 CORS 錯誤
- [ ] 前端能正常顯示資料
- [ ] Network 標籤顯示 API 請求成功（200 狀態碼）

---

## 🎉 下一步

CORS 問題解決後，您應該能夠：

1. ✅ 在前端查看任務列表
2. ✅ 新增搜尋任務
3. ✅ 查看聯絡人資料
4. ✅ 匯出資料
5. ✅ 查看系統統計資訊

如果仍有問題，請提供：
- API 服務的 Variables 截圖
- 瀏覽器控制台的錯誤訊息截圖
- API 服務的 Deploy Logs

祝您部署成功！🚀

