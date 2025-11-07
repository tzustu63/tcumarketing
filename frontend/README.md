# 慈濟大學招生通路自動開發系統 - 前端

## 專案結構

```
frontend/
├── src/
│   ├── components/          # 可重用元件
│   │   ├── Layout.js       # 主要佈局和導航
│   │   ├── TaskForm.js     # 任務建立表單
│   │   ├── TaskList.js     # 任務列表顯示
│   │   ├── ContactFilters.js  # 聯絡資訊篩選器
│   │   ├── ContactTable.js    # 聯絡資訊表格
│   │   └── Pagination.js      # 分頁元件
│   ├── pages/              # 頁面元件
│   │   ├── Dashboard.js    # 儀表板頁面
│   │   ├── Tasks.js        # 任務管理頁面
│   │   ├── Contacts.js     # 聯絡資訊瀏覽頁面
│   │   ├── Export.js       # 資料匯出頁面
│   │   └── Logs.js         # 系統日誌頁面
│   ├── services/           # API 服務層
│   │   ├── api.js          # Axios 配置和攔截器
│   │   ├── taskService.js  # 任務相關 API
│   │   ├── contactService.js  # 聯絡資訊相關 API
│   │   └── statsService.js    # 統計和日誌 API
│   ├── App.js              # 主應用元件和路由
│   ├── index.js            # 應用入口
│   └── index.css           # 全域樣式
├── public/
│   └── index.html
├── package.json
└── tailwind.config.js
```

## 功能特性

### 1. 儀表板 (Dashboard)
- 顯示系統統計資料（總任務數、已完成任務、總聯絡資訊、成功率）
- 顯示最近任務執行狀態
- 即時更新（每 10 秒自動刷新）
- 錯誤統計和分析

### 2. 任務管理 (Tasks)
- 建立新任務（關鍵字、城市、目標平台選擇）
- 任務列表顯示（狀態、進度、結果數）
- 任務啟動和刪除功能
- 自動刷新（每 5 秒）
- 進度條視覺化

### 3. 聯絡資訊瀏覽 (Contacts)
- 聯絡資訊列表顯示
- 多條件篩選（機構類型、城市、日期範圍）
- 分頁功能
- 品質分數顯示
- Email 和 WhatsApp 快速連結

### 4. 資料匯出 (Export)
- Excel 檔案匯出
- 篩選條件設定
- 匯出進度顯示
- 自動下載功能
- 中英文雙語標題

### 5. 系統日誌 (Logs)
- 爬取日誌列表
- 錯誤日誌篩選（狀態、操作類型）
- 錯誤詳情查看
- 回應時間統計
- 錯誤統計摘要

## 技術堆疊

- **React 18.2**: 前端框架
- **React Router 6**: 路由管理
- **Axios**: HTTP 客戶端
- **Tailwind CSS**: 樣式框架
- **React Scripts**: 建置工具

## 開發指南

### 安裝依賴

```bash
cd frontend
npm install
```

### 啟動開發伺服器

```bash
npm start
```

應用將在 http://localhost:3000 啟動

### 建置生產版本

```bash
npm run build
```

### 環境變數

在 `.env` 檔案中設定：

```
REACT_APP_API_URL=http://localhost:8000
```

## API 整合

所有 API 請求通過 `src/services/` 中的服務層處理：

- `taskService`: 任務 CRUD 操作
- `contactService`: 聯絡資訊查詢和匯出
- `statsService`: 統計資料和日誌

API 基礎 URL 可通過環境變數配置，預設為 `http://localhost:8000`

## 元件說明

### Layout
主要佈局元件，包含頂部導航和側邊欄

### TaskForm
任務建立表單，支援：
- 關鍵字選擇（SMA Internasional、Pusat Bahasa Mandarin、Agen Pendidikan）
- 城市選擇（印尼主要城市）
- 平台選擇（Website、Facebook、Instagram）
- 最大結果數設定

### ContactFilters
聯絡資訊篩選器，支援：
- 機構類型篩選
- 城市篩選
- 日期範圍篩選

### Pagination
通用分頁元件，支援：
- 頁碼導航
- 上一頁/下一頁
- 頁面跳轉

## 樣式指南

使用 Tailwind CSS 實用類別進行樣式設計：

- 主色調：藍色 (blue-600)
- 成功：綠色 (green-600)
- 錯誤：紅色 (red-600)
- 警告：黃色 (yellow-600)
- 中性：灰色 (gray-xxx)

## 瀏覽器支援

- Chrome (最新版)
- Firefox (最新版)
- Safari (最新版)
- Edge (最新版)

## 注意事項

1. 確保後端 API 服務正在運行
2. 開發環境使用 proxy 設定連接後端
3. 生產環境需要配置正確的 API URL
4. 所有日期使用 ISO 8601 格式
5. 檔案匯出使用瀏覽器原生下載功能
