# 添加關鍵字欄位到聯絡資訊表

## 更新日期
2025-01-05

## 更新原因
為了在聯絡資訊列表中顯示當時使用的搜尋關鍵字，需要在 `contacts` 表中添加 `keyword` 欄位。

## 更新內容

### 1. 資料庫遷移
**檔案**: `backend/alembic/versions/20250105_add_keyword_to_contacts.py`

- 在 `contacts` 表添加 `keyword` 欄位 (VARCHAR(255))
- 創建索引 `idx_contacts_keyword` 以提升查詢效能

### 2. 資料模型更新
**檔案**: `backend/app/models/contact.py`

- 在 Contact 模型添加 `keyword` 欄位

### 3. API Schema 更新
**檔案**: `backend/app/api/schemas.py`

- 在 `ContactResponse` 添加 `keyword` 欄位

### 4. 爬蟲任務更新
**檔案**: `backend/app/tasks/scraping_tasks.py`

- 在 `extract_website_task` 中，創建 contact 時包含 keyword
- 在 `extract_social_task` 中，創建 contact 時包含 keyword
- 從 task 對象獲取 keyword 並儲存到 contact_data

### 5. 前端顯示更新
**檔案**: `frontend/src/components/ContactTable.js`

- 表格標題從「類型」改為「關鍵字」
- 顯示 `contact.keyword` 而不是 `contact.institution_type`
- 國家欄位顯示完整名稱（如「印尼 (Indonesia)」）而不是代碼（如「ID」）

## 執行遷移

在 Docker 容器中執行：

```bash
docker-compose exec api alembic upgrade head
```

或在本地執行：

```bash
cd backend
alembic upgrade head
```

## 驗證

### 1. 檢查資料庫結構
```sql
\d contacts
```

應該看到 `keyword` 欄位和對應的索引。

### 2. 檢查現有資料
```sql
SELECT id, keyword, institution_name, country FROM contacts LIMIT 10;
```

現有資料的 keyword 欄位會是 NULL，新創建的聯絡資訊會包含關鍵字。

### 3. 測試前端顯示
1. 訪問 http://localhost:3000
2. 查看聯絡資訊列表
3. 確認「關鍵字」欄位顯示正確
4. 確認「國家」欄位顯示完整名稱

## 影響範圍

### 現有資料
- 現有的 contacts 記錄的 keyword 欄位會是 NULL
- 不影響現有功能
- 新創建的 contacts 會包含 keyword

### API 回應
- ContactResponse 現在包含 `keyword` 欄位
- 前端可以正確接收和顯示關鍵字

### 篩選功能
- 未來可以根據 keyword 進行篩選
- 已在 ContactFilters 組件中實現關鍵字篩選

## 後續工作

1. **資料回填**（可選）
   - 可以為現有的 contacts 回填 keyword
   - 通過 task_id 關聯到 task 表獲取 keyword

2. **篩選優化**
   - 在 API 中添加 keyword 篩選參數
   - 更新 ContactRepository 的 search 方法

3. **匯出功能**
   - 在 Excel 匯出中包含 keyword 欄位
   - 更新 ExportService

## 注意事項

- 此更新向後兼容
- 不會影響現有的 API 端點
- 前端會優雅地處理 keyword 為 NULL 的情況（顯示 "-"）
- 索引已創建，查詢效能不受影響

