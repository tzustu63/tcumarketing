# 添加關鍵字和城市篩選功能

## 更新日期
2025-01-05

## 問題描述
用戶點擊已完成的任務後，雖然會跳轉到聯絡資訊頁面並傳遞篩選條件（國家、關鍵字、城市），但後端 API 不支援 keyword 和 city 篩選參數，導致篩選無法正常工作。

## 解決方案

### 1. 後端 API 更新
**檔案**: `backend/app/api/routes/contacts.py`

#### 添加篩選參數
在 `get_contacts` 端點添加兩個新的查詢參數：
- `keyword`: 按搜尋關鍵字篩選
- `city`: 按城市篩選

```python
@router.get("", response_model=ContactListResponse)
async def get_contacts(
    # ... 其他參數
    keyword: Optional[str] = Query(None, description="Filter by search keyword"),
    city: Optional[str] = Query(None, description="Filter by city"),
    # ... 其他參數
):
```

#### 實現篩選邏輯

**關鍵字篩選**:
```python
if keyword:
    query = query.filter(Contact.keyword == keyword)
```

**城市篩選**:
由於 city 資訊儲存在 tasks 表中，需要 JOIN 查詢：
```python
if city:
    from app.models.task import Task
    query = query.join(Task, Contact.task_id == Task.id)
    query = query.filter(Task.city == city)
```

### 2. 重啟服務
```bash
docker-compose restart api
```

## 測試驗證

### API 測試
```bash
# 測試關鍵字和國家篩選
curl -G "http://localhost:8000/api/contacts" \
  --data-urlencode "country=MY" \
  --data-urlencode "keyword=独中" \
  --data-urlencode "limit=3"
```

**結果**: 
- Total: 6 筆符合條件
- 返回: 3 筆資料（limit=3）

### 完整篩選測試
```bash
# 測試國家、關鍵字、城市三個條件
curl -G "http://localhost:8000/api/contacts" \
  --data-urlencode "country=MY" \
  --data-urlencode "keyword=独中" \
  --data-urlencode "city=Kuala Lumpur" \
  --data-urlencode "limit=5"
```

## 前端整合

### 1. TaskList 點擊跳轉
當用戶點擊已完成的任務時：
```javascript
navigate('/contacts', {
  state: {
    filters: {
      country: task.country,    // ✅ 支援
      keyword: task.keyword,    // ✅ 支援
      city: task.city          // ✅ 支援
    }
  }
});
```

### 2. Contacts 頁面接收
```javascript
const initialFilters = location.state?.filters || {
  country: '',
  keyword: '',
  city: '',
};
```

### 3. ContactFilters 顯示
篩選條件會自動顯示在下拉選單中：
- 國家：馬來西亞 (Malaysia)
- 關鍵字：独中
- 城市：Kuala Lumpur

## 完整流程

### 步驟 1: 查看任務
訪問 http://localhost:3000/tasks

任務資訊：
- 國家：MY (馬來西亞)
- 關鍵字：独中
- 城市：Kuala Lumpur
- 狀態：已完成
- 結果數：6

### 步驟 2: 點擊任務
點擊已完成的任務列

### 步驟 3: 自動跳轉和篩選
跳轉到 http://localhost:3000/contacts

篩選條件自動設定：
- ✅ 國家：馬來西亞 (Malaysia)
- ✅ 關鍵字：独中
- ✅ 城市：Kuala Lumpur

### 步驟 4: 查看結果
只顯示 6 筆符合所有條件的聯絡資訊

### 步驟 5: 重置篩選
點擊「重置」按鈕，清除所有篩選條件，查看全部資料

## API 端點更新

### GET /api/contacts

**新增查詢參數**:
- `keyword` (string, optional): 按搜尋關鍵字篩選
- `city` (string, optional): 按城市篩選

**範例請求**:
```
GET /api/contacts?country=MY&keyword=独中&city=Kuala%20Lumpur&limit=10
```

**範例回應**:
```json
{
  "total": 6,
  "skip": 0,
  "limit": 10,
  "contacts": [
    {
      "id": "...",
      "country": "MY",
      "keyword": "独中",
      "institution_name": "吉隆坡莱佛士高等教育学院",
      "email": "...",
      ...
    }
  ]
}
```

## 資料庫查詢

### 關鍵字篩選
直接在 contacts 表查詢：
```sql
SELECT * FROM contacts WHERE keyword = '独中';
```

### 城市篩選
需要 JOIN tasks 表：
```sql
SELECT c.* 
FROM contacts c
JOIN tasks t ON c.task_id = t.id
WHERE t.city = 'Kuala Lumpur';
```

### 組合篩選
```sql
SELECT c.* 
FROM contacts c
JOIN tasks t ON c.task_id = t.id
WHERE c.country = 'MY'
  AND c.keyword = '独中'
  AND t.city = 'Kuala Lumpur';
```

## 效能考量

### 索引
- ✅ `idx_contacts_country`: 國家篩選已有索引
- ✅ `idx_contacts_keyword`: 關鍵字篩選已有索引
- ⚠️ tasks 表的 city 欄位可能需要索引（如果查詢變慢）

### 優化建議
如果城市篩選查詢變慢，可以考慮：
1. 在 tasks 表的 city 欄位添加索引
2. 或在 contacts 表添加 city 欄位（冗餘但更快）

## 測試檢查清單

- [x] API 支援 keyword 參數
- [x] API 支援 city 參數
- [x] 關鍵字篩選正確工作
- [x] 城市篩選正確工作
- [x] 組合篩選正確工作
- [x] 前端正確傳遞參數
- [x] 前端正確顯示篩選條件
- [x] 重置按鈕正確清除篩選
- [x] 點擊任務跳轉功能正常

## 總結

✅ 後端 API 已支援 keyword 和 city 篩選
✅ 前端已正確整合
✅ 任務點擊跳轉功能完整實現
✅ 篩選條件正確套用
✅ 用戶體驗流暢

現在用戶可以：
1. 點擊已完成的任務
2. 自動跳轉到聯絡資訊頁面
3. 自動套用國家、關鍵字、城市三個篩選條件
4. 只查看該任務的結果
5. 點擊重置查看所有資料

