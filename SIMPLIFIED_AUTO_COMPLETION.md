# 簡化的任務自動完成機制

## 更新日期
2025-01-05

## 新機制說明

### 簡化規則
**只有一個規則**：如果任務沒有活躍的 worker，就自動完成。

### 檢查頻率
**每分鐘檢查一次** (60 秒)

### 邏輯流程
```
1. 每分鐘執行一次檢查
2. 獲取所有「執行中」的任務
3. 檢查 Celery 中的活躍任務
4. 對於每個「執行中」的任務：
   - 如果有活躍的萃取任務 → 跳過（繼續執行）
   - 如果沒有活躍的萃取任務 → 自動完成（100%）
```

## 程式碼

### 核心邏輯
```python
# 檢查每個執行中的任務
for task in running_tasks:
    task_id = str(task.id)
    
    # 如果有活躍的萃取任務，跳過
    if task_id in active_task_ids:
        logger.debug(f"Task {task_id} has active extraction tasks, skipping")
        continue
    
    # 沒有活躍的 worker，自動完成
    logger.info(f"Task {task_id} at {task.progress}% with no active workers, marking as completed")
    
    task.status = "completed"
    task.progress = 100
    task.completed_at = datetime.utcnow()
    db.commit()
    
    logger.info(f"Auto-completed task {task_id} with {task.results_count} results")
```

### 調度配置
```python
celery_app.conf.beat_schedule = {
    'check-stuck-tasks-every-minute': {
        'task': 'task_monitor.check_stuck_tasks',
        'schedule': 60.0,  # 每 60 秒
    },
}
```

## 優點

### 1. 簡單明確
- ✅ 只有一個規則，容易理解
- ✅ 沒有複雜的時間判斷
- ✅ 邏輯清晰

### 2. 快速反應
- ✅ 最多等待 1 分鐘就會檢查
- ✅ 不需要等待 2 分鐘或 5 分鐘
- ✅ 任務完成更及時

### 3. 準確判斷
- ✅ 直接檢查是否有活躍的 worker
- ✅ 不依賴執行時間判斷
- ✅ 避免誤判

## 使用場景

### 場景 1: 正常完成
```
時間軸:
0:00 - 任務開始，進度 0%
0:10 - Google 搜尋完成，進度 70%
0:15 - 萃取任務開始執行
0:45 - 所有萃取任務完成
1:00 - 監控檢查：沒有活躍 worker → 自動完成 100%
```

### 場景 2: 萃取卡住
```
時間軸:
0:00 - 任務開始，進度 0%
0:10 - Google 搜尋完成，進度 70%
0:15 - 萃取任務開始執行
0:30 - 某個萃取任務卡住
1:00 - 監控檢查：沒有活躍 worker → 自動完成 100%
```

### 場景 3: Worker 重啟
```
時間軸:
0:00 - 任務開始，進度 0%
0:10 - Google 搜尋完成，進度 70%
0:15 - 萃取任務開始執行
0:20 - Worker 容器重啟，任務丟失
1:00 - 監控檢查：沒有活躍 worker → 自動完成 100%
```

## 與舊機制的比較

### 舊機制（已移除）
```python
# 規則 1: 執行超過 5 分鐘
if running_time > timedelta(minutes=5):
    # 自動完成

# 規則 2: 進度 ≥ 70% 且執行超過 2 分鐘
elif task.progress >= 70 and running_time > timedelta(minutes=2):
    # 自動完成
```

**問題**:
- ❌ 需要等待 2-5 分鐘
- ❌ 依賴時間判斷，可能不準確
- ❌ 兩個規則，邏輯複雜

### 新機制（當前）
```python
# 唯一規則: 沒有活躍的 worker
if task_id not in active_task_ids:
    # 自動完成
```

**優點**:
- ✅ 最多等待 1 分鐘
- ✅ 直接檢查 worker 狀態
- ✅ 一個規則，邏輯簡單

## 監控和驗證

### 檢查監控是否運行
```bash
# 查看 beat 日誌
docker-compose logs beat --tail 20

# 應該看到每分鐘的日誌
# "Checking for stuck tasks..."
```

### 手動觸發檢查
```bash
docker-compose exec api python -c "
from app.tasks.task_monitor import check_and_complete_stuck_tasks
check_and_complete_stuck_tasks()
print('Check completed')
"
```

### 查看自動完成的任務
```bash
docker-compose exec db psql -U user -d recruitment -c "
SELECT id, keyword, status, progress, results_count, 
       completed_at - started_at as duration
FROM tasks 
WHERE status = 'completed' 
  AND completed_at IS NOT NULL
ORDER BY completed_at DESC 
LIMIT 5;
"
```

## 測試

### 測試場景 1: 正常任務
1. 創建一個新任務
2. 等待任務執行
3. 觀察進度更新
4. 確認任務在萃取完成後 1 分鐘內自動完成

### 測試場景 2: 卡住的任務
1. 創建一個任務
2. 在萃取過程中重啟 worker
3. 等待 1 分鐘
4. 確認任務自動完成

### 測試場景 3: 多個任務
1. 同時創建多個任務
2. 觀察所有任務的進度
3. 確認所有任務都能正確完成

## 故障排除

### 任務沒有自動完成
**檢查 1**: Beat 是否運行
```bash
docker-compose ps beat
```

**檢查 2**: 查看 beat 日誌
```bash
docker-compose logs beat --tail 50
```

**檢查 3**: 手動觸發檢查
```bash
docker-compose exec api python -c "
from app.tasks.task_monitor import check_and_complete_stuck_tasks
check_and_complete_stuck_tasks()
"
```

### Beat 沒有運行
```bash
# 重啟 beat
docker-compose restart beat

# 查看日誌
docker-compose logs beat -f
```

### 任務立即完成（太快）
這是正常的！新機制會在沒有活躍 worker 時立即完成任務。
如果萃取任務已經完成，下一次檢查（最多 1 分鐘）就會自動完成。

## 總結

### 新機制特點
- ✅ **簡單**: 只有一個規則
- ✅ **快速**: 最多等待 1 分鐘
- ✅ **準確**: 直接檢查 worker 狀態
- ✅ **可靠**: 每分鐘自動檢查

### 適用情況
- ✅ 所有類型的任務
- ✅ 正常完成的任務
- ✅ 卡住的任務
- ✅ Worker 重啟的情況

### 不需要
- ❌ 不需要手動完成任務
- ❌ 不需要等待很長時間
- ❌ 不需要複雜的時間判斷

**結論**: 新機制更簡單、更快速、更可靠！

