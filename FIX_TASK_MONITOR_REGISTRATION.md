# 修正任務監控註冊問題

## 問題描述
任務監控功能無法正常工作，Beat 發送任務但 Worker 無法執行，錯誤訊息：
```
Received unregistered task of type 'task_monitor.check_stuck_tasks'
KeyError: 'task_monitor.check_stuck_tasks'
```

## 根本原因
`task_monitor.py` 中的任務沒有被 Worker 發現和註冊，因為：
1. `app/tasks/__init__.py` 沒有導入 `task_monitor` 模組
2. Celery 的 `autodiscover_tasks` 無法自動發現未導入的模組

## 解決方案

### 1. 在 `app/tasks/__init__.py` 中導入任務
**檔案**: `backend/app/tasks/__init__.py`

```python
from .task_monitor import check_stuck_tasks_task

__all__ = [
    # ... 其他任務
    "check_stuck_tasks_task"
]
```

### 2. 確保 Beat Schedule 使用正確的任務名稱
**檔案**: `backend/app/celery_app.py`

```python
celery_app.conf.beat_schedule = {
    'check-stuck-tasks-every-minute': {
        'task': 'task_monitor.check_stuck_tasks',  # 使用裝飾器中定義的名稱
        'schedule': 60.0,
    },
}
```

### 3. 重啟服務
```bash
docker-compose restart worker beat
```

## 驗證步驟

### 1. 檢查任務是否已註冊
```bash
docker-compose exec worker celery -A app.celery_app inspect registered | grep task_monitor
```

**預期輸出**:
```
* task_monitor.check_stuck_tasks
```

### 2. 檢查 Beat 是否發送任務
```bash
docker-compose logs beat --tail 20 | grep check-stuck
```

**預期輸出**:
```
Scheduler: Sending due task check-stuck-tasks-every-minute
```

### 3. 檢查 Worker 是否執行任務
```bash
docker-compose logs worker --tail 30 | grep "Checking for stuck"
```

**預期輸出**:
```
Checking for stuck tasks...
```

### 4. 驗證自動完成功能
```bash
# 手動觸發檢查
docker-compose exec api python -c "
from app.tasks.task_monitor import check_and_complete_stuck_tasks
check_and_complete_stuck_tasks()
"
```

## 測試結果

### 修正前
- ❌ Worker 無法找到任務
- ❌ 錯誤: `KeyError: 'task_monitor.check_stuck_tasks'`
- ❌ 任務卡在 70% 無法自動完成

### 修正後
- ✅ Worker 成功註冊任務
- ✅ Beat 每分鐘發送任務
- ✅ Worker 成功執行檢查
- ✅ 卡住的任務自動完成到 100%

## 執行日誌

### 成功的執行日誌
```
[2025-11-03 18:19:48] Task task_monitor.check_stuck_tasks received
[2025-11-03 18:19:48] Task starting with args=[], kwargs={}
[2025-11-03 18:19:48] Checking for stuck tasks...
[2025-11-03 18:19:48] Task succeeded in 0.066s
[2025-11-03 18:19:48] Task completed with state=SUCCESS
```

### 自動完成任務的日誌
```
Task b90db0ff-56b2-403e-a5c8-3941db4b2a2a at 70% with no active workers, marking as completed
Auto-completed task b90db0ff-56b2-403e-a5c8-3941db4b2a2a with 5 results
```

## 關鍵學習點

### 1. Celery 任務註冊
Celery 需要明確導入任務才能註冊：
```python
# 不夠 - 只定義任務
@celery_app.task(name="task_monitor.check_stuck_tasks")
def check_stuck_tasks_task():
    pass

# 需要 - 在 __init__.py 中導入
from .task_monitor import check_stuck_tasks_task
```

### 2. 任務名稱一致性
Beat Schedule 中的任務名稱必須與裝飾器中的 `name` 參數一致：
```python
# 裝飾器
@celery_app.task(name="task_monitor.check_stuck_tasks")

# Beat Schedule
'task': 'task_monitor.check_stuck_tasks'  # 必須一致
```

### 3. 驗證方法
使用 `celery inspect registered` 檢查任務是否已註冊：
```bash
celery -A app.celery_app inspect registered
```

## 預防措施

### 1. 添加新任務時的檢查清單
- [ ] 在任務檔案中定義任務
- [ ] 在 `__init__.py` 中導入任務
- [ ] 如果是定期任務，在 `beat_schedule` 中配置
- [ ] 重啟 Worker 和 Beat
- [ ] 驗證任務已註冊
- [ ] 測試任務執行

### 2. 自動化測試
可以添加測試來驗證所有任務都已註冊：
```python
def test_all_tasks_registered():
    from app.celery_app import celery_app
    registered_tasks = celery_app.tasks.keys()
    
    expected_tasks = [
        'task_monitor.check_stuck_tasks',
        'scraping_tasks.scrape_google_task',
        # ... 其他任務
    ]
    
    for task in expected_tasks:
        assert task in registered_tasks
```

## 總結

### 問題
- Worker 無法找到 `task_monitor.check_stuck_tasks` 任務

### 原因
- 任務沒有在 `__init__.py` 中導入

### 解決
- 在 `app/tasks/__init__.py` 中導入 `check_stuck_tasks_task`
- 重啟 Worker 和 Beat

### 結果
- ✅ 任務成功註冊
- ✅ 每分鐘自動檢查
- ✅ 卡住的任務自動完成
- ✅ 系統正常運行

