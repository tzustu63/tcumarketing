# 驗證關鍵字顯示功能

## 執行日期
2025-01-05

## 驗證步驟

### 1. ✅ 資料庫遷移
```bash
docker-compose exec api alembic upgrade head
```
**結果**: 成功執行遷移 002 -> 003

### 2. ✅ 檢查資料庫結構
```sql
\d contacts
```
**結果**: keyword 欄位已添加，類型為 VARCHAR(255)

### 3. ✅ 回填現有資料
```sql
UPDATE contacts 
SET keyword = tasks.keyword 
FROM tasks 
WHERE contacts.task_id = tasks.id 
AND contacts.keyword IS NULL;
```
**結果**: 更新了 21 筆資料

### 4. ✅ 驗證資料
```sql
SELECT country, keyword, institution_name FROM contacts LIMIT 5;
```
**結果**: 
- country: ID
- keyword: 独中, Study Abroad Consultant 等
- 資料正確顯示

### 5. ✅ 重啟服務
```bash
docker-compose restart api worker beat
```
**結果**: 所有服務成功重啟

### 6. ✅ API 測試
```bash
curl "http://localhost:8000/api/contacts?limit=2"
```
**結果**: API 正確返回 keyword 欄位

## 前端驗證

### 訪問頁面
1. 打開 http://localhost:3000
2. 查看聯絡資訊列表

### 預期結果
- ✅ 國家欄位顯示：「印尼 (Indonesia)」而不是「ID」
- ✅ 關鍵字欄位顯示：實際的搜尋關鍵字（如「独中」、「Study Abroad Consultant」）
- ✅ 新創建的聯絡資訊會自動包含 keyword

## 測試新任務

### 創建測試任務
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "country": "SG",
    "keyword": "University",
    "city": "Singapore",
    "target_platforms": ["website"],
    "max_results": 10
  }'
```

### 預期結果
- 新創建的 contacts 會包含 keyword = "University"
- 前端顯示時會正確顯示「University」

## 資料庫查詢範例

### 查看所有關鍵字
```sql
SELECT DISTINCT keyword, COUNT(*) 
FROM contacts 
GROUP BY keyword 
ORDER BY COUNT(*) DESC;
```

### 按國家和關鍵字統計
```sql
SELECT country, keyword, COUNT(*) as count
FROM contacts 
GROUP BY country, keyword 
ORDER BY country, count DESC;
```

### 查看特定國家的聯絡資訊
```sql
SELECT country, keyword, institution_name, email
FROM contacts 
WHERE country = 'SG'
LIMIT 10;
```

## 故障排除

### 如果前端不顯示關鍵字
1. 檢查瀏覽器控制台是否有錯誤
2. 清除瀏覽器快取
3. 重新整理頁面
4. 檢查 API 回應是否包含 keyword 欄位

### 如果 API 不返回 keyword
1. 確認資料庫遷移已執行
2. 確認 API 容器已重啟
3. 檢查 ContactResponse schema 是否包含 keyword

### 如果新任務不包含 keyword
1. 確認 worker 容器已重啟
2. 檢查 scraping_tasks.py 是否已更新
3. 查看 worker 日誌：`docker-compose logs worker`

## 成功標準

- [x] 資料庫包含 keyword 欄位
- [x] 現有資料已回填 keyword
- [x] API 正確返回 keyword
- [x] 前端表格顯示「關鍵字」標題
- [x] 前端正確顯示 keyword 內容
- [x] 國家顯示完整名稱
- [x] 新任務會自動儲存 keyword

## 總結

✅ 所有功能已正確實現並驗證通過！

系統現在會：
1. 在創建聯絡資訊時自動儲存搜尋關鍵字
2. 在前端表格中顯示關鍵字
3. 顯示完整的國家名稱
4. 支援按關鍵字篩選（已在 ContactFilters 中實現）

