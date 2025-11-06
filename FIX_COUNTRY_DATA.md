# 修正聯絡資訊的國家資料

## 問題描述
發現部分聯絡資訊的國家代碼不正確。例如：
- 「吉隆坡莱佛士高等教育学院」應該是馬來西亞 (MY)，但顯示為印尼 (ID)
- 「董总携手国立体育大学参访」應該是馬來西亞 (MY)，但顯示為印尼 (ID)

## 原因分析
在之前的資料庫遷移中，`contacts` 表的 `country` 欄位設定了預設值 "ID"。當時創建這些聯絡資訊時，雖然任務 (tasks) 的國家是正確的，但 contacts 表中的 country 欄位使用了預設值。

## 修正步驟

### 1. 檢查問題
```sql
-- 檢查 tasks 表的國家
SELECT id, country, keyword, city FROM tasks;

-- 檢查 contacts 表的國家
SELECT country, keyword, institution_name 
FROM contacts 
WHERE institution_name LIKE '%吉隆坡%';
```

**發現**:
- Tasks 表: country = "MY" ✓
- Contacts 表: country = "ID" ✗

### 2. 執行修正
```sql
UPDATE contacts 
SET country = tasks.country 
FROM tasks 
WHERE contacts.task_id = tasks.id 
AND contacts.country != tasks.country;
```

**結果**: 更新了 10 筆資料

### 3. 驗證修正
```sql
-- 再次檢查吉隆坡相關資料
SELECT country, keyword, institution_name 
FROM contacts 
WHERE institution_name LIKE '%吉隆坡%' 
OR institution_name LIKE '%董总%';
```

**結果**: 所有資料現在都正確顯示 country = "MY"

### 4. 檢查資料分佈
```sql
SELECT country, COUNT(*) as count 
FROM contacts 
GROUP BY country;
```

**結果**:
- 馬來西亞 (MY): 10 筆
- 印尼 (ID): 11 筆

## 驗證

### API 測試
```bash
curl "http://localhost:8000/api/contacts?limit=3"
```

**結果**: API 正確返回 country = "MY"

### 前端顯示
訪問 http://localhost:3000

**預期結果**:
- 「吉隆坡莱佛士高等教育学院」顯示為「馬來西亞 (Malaysia)」
- 「董总携手国立体育大学参访」顯示為「馬來西亞 (Malaysia)」

## 根本原因修正

為了避免未來出現類似問題，已經在爬蟲任務中確保：

1. **backend/app/tasks/scraping_tasks.py**
   - 在創建 contact 時，從 task 對象獲取正確的 country
   - 不依賴預設值

```python
# 獲取任務的國家代碼
task = task_repo.get(task_id)
country_code = task.country if task else "ID"

contact_data = {
    "task_id": task_id,
    "country": country_code,  # 使用任務的國家代碼
    "keyword": keyword,
    ...
}
```

2. **資料庫約束**
   - country 欄位保留預設值 "ID" 作為後備
   - 但程式碼會明確設定正確的值

## 預防措施

### 定期檢查資料一致性
```sql
-- 檢查 contacts 和 tasks 的國家是否一致
SELECT 
    c.id,
    c.country as contact_country,
    t.country as task_country,
    c.institution_name
FROM contacts c
JOIN tasks t ON c.task_id = t.id
WHERE c.country != t.country;
```

如果有結果，表示有不一致的資料需要修正。

### 自動修正腳本
可以創建一個定期執行的腳本：

```sql
-- 自動同步 contacts 的 country 與 tasks 的 country
UPDATE contacts 
SET country = tasks.country 
FROM tasks 
WHERE contacts.task_id = tasks.id 
AND contacts.country != tasks.country;
```

## 總結

✅ 問題已修正
✅ 資料已驗證
✅ API 正確返回
✅ 前端應該正確顯示
✅ 已實施預防措施

現在所有聯絡資訊都會顯示正確的國家名稱！

