# 任務進度追蹤改進

**日期**: 2025-11-03  
**改進類型**: 進度顯示準確性

---

## 🎯 問題描述

### 原始問題
任務進度顯示不準確：
- ❌ 主任務完成搜尋後立即顯示 100%
- ❌ 但子任務（網站萃取）還在執行中
- ❌ 使用者看到 100% 但實際上還有工作在進行
- ❌ 無法準確了解真實完成狀態

### 範例情況
```
任務狀態: completed ✅
進度: 100% ✅
但是...
Worker 狀態: 4 個活動任務正在運行 🔄
```

這會讓使用者困惑：任務已經完成了嗎？為什麼還有 Worker 在運行？

---

## ✅ 解決方案

### 新的進度計算邏輯

**進度階段**:
1. **0-10%**: 初始化和配置
2. **10-50%**: Google 搜尋中
3. **50-70%**: 搜尋完成，準備萃取
4. **70-95%**: 網站萃取進行中（子任務執行）
5. **95-100%**: 所有子任務完成，最終處理
6. **100%**: 真正完成（所有 Worker 都結束）

### 實作方式

使用 Celery 的 `chord` 模式：
```python
# 主任務創建子任務
chord(extraction_tasks)(
    mark_task_completed.s(task_id, total_tasks)
)
```

**工作流程**:
```
主任務 (scrape_google_task)
  ├─ 0%: 開始
  ├─ 10%: 搜尋開始
  ├─ 50%: 搜尋完成
  ├─ 70%: 創建子任務
  │
  ├─ 子任務 1 (extract_website_task) 🔄
  ├─ 子任務 2 (extract_website_task) 🔄
  ├─ 子任務 3 (extract_website_task) 🔄
  └─ 子任務 N (extract_website_task) 🔄
       │
       └─ 所有子任務完成 ✅
            │
            └─ 回調任務 (mark_task_completed)
                 └─ 100%: 真正完成 ✅
```

---

## 📝 修改的程式碼

### 1. 主任務進度更新

**修改前**:
```python
# Execute extraction tasks
from celery import group
job = group(extraction_tasks)
result = job.apply_async()

# 立即標記為完成 ❌
task.progress = 100
task.status = "completed"
task.completed_at = datetime.utcnow()
db.commit()
```

**修改後**:
```python
# Execute extraction tasks
from celery import chord

if extraction_tasks:
    # 保持在 70%，等待子任務完成 ✅
    task.progress = 70
    db.commit()
    
    # 使用 chord 等待所有子任務完成
    job = chord(extraction_tasks)(
        mark_task_completed.s(task_id, len(extraction_tasks))
    )
else:
    # 沒有子任務，直接完成
    task.progress = 100
    task.status = "completed"
    task.completed_at = datetime.utcnow()
    db.commit()
```

### 2. 新增完成回調任務

```python
@celery_app.task(name="scraping_tasks.mark_task_completed")
def mark_task_completed(results, task_id: str, total_tasks: int):
    """
    所有子任務完成後的回調，標記主任務為完成。
    """
    db = SessionLocal()
    task_repo = TaskRepository(db)
    
    try:
        task = task_repo.get(task_id)
        if task:
            # 現在才真正標記為 100% ✅
            task.progress = 100
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Task {task_id} completed with {task.results_count} results")
    finally:
        db.close()
```

### 3. 子任務進度更新

每個子任務完成時更新進度：
```python
# 在 extract_website_task 和 extract_social_task 結束時
_update_extraction_progress(db, task_id)
```

---

## 📊 進度顯示對比

### 修改前

| 時間 | 主任務狀態 | 進度 | Worker 狀態 | 問題 |
|------|-----------|------|------------|------|
| T+0s | running | 0% | 0 個任務 | ✅ 正確 |
| T+5s | running | 50% | 0 個任務 | ✅ 正確 |
| T+10s | **completed** | **100%** | **7 個任務** | ❌ 不準確！ |
| T+30s | completed | 100% | 3 個任務 | ❌ 混亂 |
| T+60s | completed | 100% | 0 個任務 | ✅ 真正完成 |

### 修改後

| 時間 | 主任務狀態 | 進度 | Worker 狀態 | 說明 |
|------|-----------|------|------------|------|
| T+0s | running | 0% | 0 個任務 | ✅ 初始化 |
| T+5s | running | 50% | 0 個任務 | ✅ 搜尋中 |
| T+10s | **running** | **70%** | **7 個任務** | ✅ 萃取中 |
| T+30s | running | 85% | 3 個任務 | ✅ 進行中 |
| T+60s | **completed** | **100%** | **0 個任務** | ✅ 真正完成！ |

---

## 🎯 使用者體驗改善

### 修改前的使用者體驗
```
使用者: "任務顯示 100% 完成了！"
系統: 但還有 7 個 Worker 在運行...
使用者: "那到底完成了沒有？😕"
```

### 修改後的使用者體驗
```
使用者: "任務顯示 70%，還在萃取網站"
系統: 有 7 個 Worker 正在工作
使用者: "好的，我知道還在進行中 👍"

[等待一段時間...]

使用者: "現在顯示 100% 完成了！"
系統: 0 個 Worker 在運行
使用者: "太好了，真的完成了！✅"
```

---

## 📈 進度計算公式

### 階段權重
```python
# 搜尋階段: 0-70%
search_progress = 70

# 萃取階段: 70-100%
extraction_progress = 30

# 總進度
total_progress = search_progress + (completed_tasks / total_tasks) * extraction_progress
```

### 範例計算
```
假設有 10 個網站要萃取：

完成 0/10: 70% (搜尋完成，開始萃取)
完成 3/10: 79% (70 + 3/10 * 30)
完成 5/10: 85% (70 + 5/10 * 30)
完成 8/10: 94% (70 + 8/10 * 30)
完成 10/10: 100% (真正完成！)
```

---

## 🔧 技術細節

### Celery Chord 模式

**什麼是 Chord？**
- 一組並行任務 + 一個回調任務
- 所有並行任務完成後，自動執行回調
- 完美適合我們的場景

**語法**:
```python
from celery import chord

# 創建 chord
result = chord(
    [task1.s(), task2.s(), task3.s()]  # 並行任務
)(
    callback_task.s()  # 回調任務
)
```

**執行流程**:
```
task1 ─┐
task2 ─┼─> 全部完成 ─> callback_task
task3 ─┘
```

### 進度追蹤函數

```python
def _update_extraction_progress(db: Session, task_id: str):
    """
    更新萃取進度（70-95%）
    最終的 100% 由 mark_task_completed 設定
    """
    # 檢查還有多少活動任務
    # 根據剩餘任務數計算進度
    # 保持在 70-95% 之間
```

---

## ✅ 測試驗證

### 測試步驟

1. **創建新任務**
   ```bash
   curl -X POST "http://localhost:8000/api/tasks" \
     -H "Content-Type: application/json" \
     -d '{
       "keyword": "Test",
       "city": "Jakarta",
       "country": "ID",
       "target_platforms": ["website"],
       "max_results": 10
     }'
   ```

2. **監控進度**
   ```bash
   # 每 5 秒查看一次
   watch -n 5 'curl -s "http://localhost:8000/api/tasks/{task_id}" | jq "{status, progress}"'
   ```

3. **檢查 Worker**
   ```bash
   curl -s "http://localhost:8000/api/system/workers/status" | jq '.total_active'
   ```

### 預期結果

```
時間 0s:  status: "running",  progress: 0,   workers: 0
時間 5s:  status: "running",  progress: 50,  workers: 0
時間 10s: status: "running",  progress: 70,  workers: 10
時間 30s: status: "running",  progress: 85,  workers: 5
時間 60s: status: "completed", progress: 100, workers: 0 ✅
```

---

## 📚 相關文檔

- **Celery Chord 文檔**: https://docs.celeryq.dev/en/stable/userguide/canvas.html#chords
- **任務管理**: `backend/app/tasks/scraping_tasks.py`
- **系統就緒指南**: `docs/SYSTEM_READY.md`

---

## 🎉 總結

### 改進成果
- ✅ 進度顯示準確反映真實完成狀態
- ✅ 100% 表示所有工作真正完成
- ✅ 使用者可以清楚了解任務進度
- ✅ 不再有混亂的狀態顯示

### 使用者好處
- ✅ 更清晰的進度資訊
- ✅ 更好的使用者體驗
- ✅ 更準確的完成時間預估
- ✅ 減少困惑和疑問

**進度追蹤現在更準確了！** 🎯
