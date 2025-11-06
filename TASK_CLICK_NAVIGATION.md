# 任務點擊導航功能

## 功能描述
當任務狀態為「已完成」時，點擊任務列可以直接跳轉到聯絡資訊頁面，並自動套用該任務的篩選條件（國家、關鍵字、城市）。

## 實現日期
2025-01-05

## 更新內容

### 1. TaskList 組件更新
**檔案**: `frontend/src/components/TaskList.js`

#### 新增功能
- 導入 `useNavigate` from react-router-dom
- 添加 `handleTaskClick` 函數處理任務點擊
- 已完成的任務列添加 hover 效果和游標指標
- 狀態標籤添加箭頭圖示提示可點擊
- 刪除按鈕添加 `stopPropagation` 防止觸發列點擊

#### 程式碼變更
```javascript
// 導入 useNavigate
import { useNavigate } from 'react-router-dom';

// 添加點擊處理函數
const handleTaskClick = (task) => {
  if (task.status === 'completed') {
    navigate('/contacts', {
      state: {
        filters: {
          country: task.country,
          keyword: task.keyword,
          city: task.city
        }
      }
    });
  }
};

// 任務列添加點擊事件和樣式
<tr 
  onClick={() => handleTaskClick(task)}
  className={task.status === 'completed' ? 'cursor-pointer hover:bg-gray-50' : ''}
>
```

### 2. Contacts 頁面更新
**檔案**: `frontend/src/pages/Contacts.js`

#### 新增功能
- 導入 `useLocation` from react-router-dom
- 從 navigation state 讀取初始篩選條件
- 如果有傳入篩選條件，自動套用

#### 程式碼變更
```javascript
// 導入 useLocation
import { useLocation } from 'react-router-dom';

// 從 location state 獲取篩選條件
const location = useLocation();
const initialFilters = location.state?.filters || {
  country: '',
  keyword: '',
  institution_type: '',
  city: '',
};

const [filters, setFilters] = useState(initialFilters);
```

### 3. ContactFilters 組件更新
**檔案**: `frontend/src/components/ContactFilters.js`

#### 新增功能
- 添加 `useEffect` 監聽 filters prop 變化
- 當 filters prop 更新時，同步更新 localFilters

#### 程式碼變更
```javascript
// 監聽 filters prop 變化
useEffect(() => {
  setLocalFilters(filters);
}, [filters]);
```

## 使用流程

### 1. 查看任務列表
訪問 http://localhost:3000/tasks

### 2. 識別已完成任務
- 狀態顯示「已完成」（綠色標籤）
- 滑鼠移到任務列上會顯示 hover 效果
- 狀態標籤旁有箭頭圖示 →

### 3. 點擊任務
點擊任何「已完成」的任務列

### 4. 自動跳轉和篩選
- 自動跳轉到聯絡資訊頁面 (/contacts)
- 自動套用該任務的篩選條件：
  - 國家：該任務的國家
  - 關鍵字：該任務的搜尋關鍵字
  - 城市：該任務的城市

### 5. 查看篩選結果
只顯示符合該任務條件的聯絡資訊

### 6. 重置篩選
點擊「重置」按鈕可以清除篩選條件，查看所有資料

## 範例

### 任務資訊
- 國家：馬來西亞 (MY)
- 關鍵字：独中
- 城市：Kuala Lumpur
- 狀態：已完成
- 結果數：6

### 點擊後
跳轉到聯絡資訊頁面，篩選條件自動設定為：
- 國家：馬來西亞 (Malaysia)
- 關鍵字：独中
- 城市：Kuala Lumpur

只顯示這 6 筆符合條件的聯絡資訊。

## 視覺提示

### 已完成任務
- ✅ 綠色「已完成」標籤
- ✅ 箭頭圖示 (→)
- ✅ 滑鼠游標變為指標 (cursor-pointer)
- ✅ Hover 時背景變淺灰色

### 其他狀態任務
- 等待中：灰色標籤，不可點擊
- 執行中：藍色標籤，不可點擊
- 失敗：紅色標籤，不可點擊

## 技術細節

### React Router 狀態傳遞
使用 `navigate` 的 `state` 參數傳遞篩選條件：
```javascript
navigate('/contacts', {
  state: {
    filters: { country, keyword, city }
  }
});
```

### 接收狀態
使用 `useLocation` hook 接收：
```javascript
const location = useLocation();
const filters = location.state?.filters;
```

### 防止事件冒泡
刪除按鈕使用 `stopPropagation` 防止觸發列點擊：
```javascript
onClick={(e) => {
  e.stopPropagation();
  onDelete(task.id);
}}
```

## 優點

1. **快速查看結果**：一鍵查看任務的所有聯絡資訊
2. **自動篩選**：無需手動設定篩選條件
3. **直觀操作**：視覺提示清楚，操作簡單
4. **靈活性**：可以重置篩選查看所有資料
5. **用戶體驗**：減少操作步驟，提升效率

## 測試檢查清單

- [x] 點擊已完成任務可以跳轉
- [x] 篩選條件正確套用
- [x] 顯示正確的聯絡資訊數量
- [x] 重置按鈕可以清除篩選
- [x] 刪除按鈕不會觸發跳轉
- [x] 非已完成任務不可點擊
- [x] Hover 效果正確顯示
- [x] 箭頭圖示正確顯示

## 未來改進

1. **麵包屑導航**：顯示「任務 > 聯絡資訊」路徑
2. **返回按鈕**：快速返回任務列表
3. **任務資訊顯示**：在聯絡資訊頁面顯示當前篩選來自哪個任務
4. **URL 參數**：將篩選條件加入 URL，支援分享和書籤

