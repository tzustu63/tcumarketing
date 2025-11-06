# 任務進度更新機制說明

## 概述
系統使用多階段進度更新機制，從 0% 到 100%，並有自動完成機制處理卡住的任務。

## 進度階段

### 階段 1: 初始化 (0%)
**時機**: 任務開始執行
```python
task.status = "running"
task.started_at = datetime.utcnow()
task.progress = 0
```

### 階段 2: Google 搜尋開始 (10%)
**時機**: 開始執行 Google 搜尋
```python
task.progress = 10
```

**動作**:
- 使用 Google Custom Search API（如果已配置）
- 或使用網頁爬蟲方式搜尋

### 階段 3: 搜尋完成 (50%)
**時機**: Google 搜尋完成，開始篩選結果
```python
task.progress = 50
```

**動作**:
- 篩選符合目標平台的結果
- 記錄搜尋日誌

### 階段 4: 準備萃取 (70%)
**時機**: 搜尋結果篩選完成，準備開始萃取聯絡資訊
```python
task.progress = 70
```

**動作**:
- 為每個搜尋結果創建萃取任務
- 將萃取任務加入佇列

### 階段 5: 萃取進行中 (70-95%)
**時機**: 萃取任務執行中
```python
# 保持在 70-95% 之間
current_progress = min(95, task.progress)
task.progress = current_progress
```

**特點**:
- 進度不會超過 95%，直到所有萃取任務完成
- 系統會檢查是否還有活躍的萃取任務

### 階段 6: 完成 (100%)
**時機**: 所有萃取任務完成
```python
task.progress = 100
task.status = "completed"
task.completed_at = datetime.utcnow()
```

## 自動完成機制

系統有兩個自動完成條件，防止任務永遠卡在「執行中」狀態：

### 條件 1: 長時間執行（5 分鐘）
```python
if running_time > timedelta(minutes=5):
    # 自動標記為完成
    task.status = "completed"
    task.progress = 100
```

**觸發條件**:
- 任務執行超過 5 分鐘
- 沒有活躍的萃取任務

**原因**: 任務可能因為錯誤或網路問題卡住

### 條件 2: 高進度無活動（2 分鐘）
```python
if task.progress >= 70 and running_time > timedelta(minutes=2):
    # 自動標記為完成
    task.status = "completed"
    task.progress = 100
```

**觸發條件**:
- 進度達到 70% 或以上
- 執行超過 2 分鐘
- 沒有活躍的萃取任務

**原因**: 搜尋已完成，萃取任務可能已經完成但沒有正確更新狀態

## 監控機制

### Task Monitor
**檔案**: `backend/app/tasks/task_monitor.py`

**功能**:
- 定期檢查所有「執行中」的任務
- 檢查是否有活躍的萃取任務
- 自動完成符合條件的卡住任務

**執行頻率**: 每分鐘執行一次（由 Celery Beat 調度）

### 檢查流程
```python
1. 獲取所有「執行中」的任務
2. 從 Celery 獲取活躍任務列表
3. 識別哪些任務有活躍的萃取任務
4. 對於沒有活躍萃取任務的任務：
   - 檢查執行時間
   - 檢查進度
   - 決定是否自動完成
```

## 你的情況分析

### 觀察到的狀態
- 進度: 70%
- 狀態: 執行中
- 時間: 2025/11/3 下午 5:59:47

### 可能的原因

#### 1. 正常情況
萃取任務正在執行中：
- 進度 70% 表示 Google 搜尋已完成
- 系統正在萃取聯絡資訊
- 這是正常的，需要等待萃取完成

#### 2. 萃取任務卡住
可能的原因：
- 網站回應緩慢
- 網路連線問題
- 反爬蟲機制阻擋

**解決方案**: 
- 等待 2 分鐘，系統會自動完成（條件 2）
- 或等待 5 分鐘，系統會自動完成（條件 1）

#### 3. Celery Worker 問題
Worker 可能沒有正常執行：
- Worker 容器重啟
- Worker 記憶體不足
- Worker 處理其他任務

**檢查方法**:
```bash
# 檢查 worker 狀態
docker-compose logs worker --tail 50

# 檢查活躍任務
docker-compose exec api python -c "
from app.celery_app import celery_app
inspect = celery_app.control.inspect()
print(inspect.active())
"
```

## 手動檢查和修正

### 1. 檢查任務狀態
```bash
docker-compose exec db psql -U user -d recruitment -c "
SELECT id, keyword, status, progress, started_at, 
       EXTRACT(EPOCH FROM (NOW() - started_at))/60 as minutes_running
FROM tasks 
WHERE status = 'running'
ORDER BY started_at DESC;
"
```

### 2. 檢查活躍的 Celery 任務
```bash
docker-compose exec api python -c "
from app.celery_app import celery_app
inspect = celery_app.control.inspect()
active = inspect.active()
if active:
    for worker, tasks in active.items():
        print(f'Worker: {worker}')
        for task in tasks:
            print(f'  - {task[\"name\"]}: {task[\"id\"]}')
else:
    print('No active tasks')
"
```

### 3. 手動完成卡住的任務
```bash
docker-compose exec db psql -U user -d recruitment -c "
UPDATE tasks 
SET status = 'completed', 
    progress = 100, 
    completed_at = NOW()
WHERE status = 'running' 
  AND started_at < NOW() - INTERVAL '5 minutes';
"
```

### 4. 觸發監控檢查
```bash
docker-compose exec api python -c "
from app.tasks.task_monitor import check_and_complete_stuck_tasks
check_and_complete_stuck_tasks()
print('Stuck tasks check completed')
"
```

## 改進建議

### 1. 更細緻的進度更新
可以根據萃取任務的完成比例更新進度：
```python
# 70% + (完成的萃取任務數 / 總萃取任務數) * 30%
completed_extractions = task.results_count
total_extractions = len(extraction_tasks)
progress = 70 + int((completed_extractions / total_extractions) * 30)
task.progress = min(95, progress)
```

### 2. 即時進度推送
使用 WebSocket 或 Server-Sent Events 即時推送進度更新到前端。

### 3. 更詳細的狀態資訊
在 task 表添加 `status_detail` 欄位：
- "searching": 正在搜尋
- "extracting": 正在萃取 (X/Y)
- "completing": 正在完成

### 4. 萃取任務超時設定
為每個萃取任務設定超時時間（如 60 秒），避免單個任務卡住整個流程。

## 總結

你看到的 70% 進度是正常的，表示：
1. ✅ Google 搜尋已完成
2. ✅ 搜尋結果已篩選
3. ✅ 萃取任務已加入佇列
4. ⏳ 正在萃取聯絡資訊

**預期行為**:
- 如果萃取正常進行：幾分鐘內會完成到 100%
- 如果萃取卡住：2-5 分鐘後會自動完成

**建議**:
- 等待 2-5 分鐘讓系統自動完成
- 或檢查 worker 日誌查看是否有錯誤
- 或手動觸發監控檢查

