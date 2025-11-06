# Celery Worker 配置說明

## 當前配置

### Worker 數量
**目前配置**: 10 個並行 Worker

### 配置來源
- **環境變數**: `TASK_MAX_WORKERS=10` (在 .env 文件中)
- **Docker Compose**: `--concurrency=${TASK_MAX_WORKERS:-4}`
- **實際運行**: 10 個 worker 進程

### 進程列表
```
主進程 (PID 1)  - Celery 主控制進程
Worker 1 (PID 17) - 工作進程
Worker 2 (PID 18) - 工作進程
Worker 3 (PID 19) - 工作進程
Worker 4 (PID 20) - 工作進程
Worker 5 (PID 21) - 工作進程
Worker 6 (PID 22) - 工作進程
Worker 7 (PID 23) - 工作進程
Worker 8 (PID 24) - 工作進程
Worker 9 (PID 25) - 工作進程
Worker 10 (PID 26) - 工作進程
```

## Worker 配置詳情

### Celery 配置
```python
# 並行模式: prefork (多進程)
implementation: celery.concurrency.prefork:TaskPool
max-concurrency: 10
max-tasks-per-child: 1000
```

### 任務佇列
```
佇列名稱: celery
優先級: 支援 (x-max-priority: 10)
持久化: 是 (durable: True)
```

## 效能分析

### 當前配置 (10 Workers)

**優點**:
- ✅ 可以同時處理 10 個任務
- ✅ 適合中等規模的爬蟲工作
- ✅ 記憶體使用合理 (~1.1-1.4GB 總計)

**適用場景**:
- 同時執行多個搜尋任務
- 並行萃取多個網站的聯絡資訊
- 處理多個國家的任務

### 記憶體使用
```
每個 Worker: ~110-145 MB
總計: ~1.2-1.5 GB
```

## 調整建議

### 增加 Workers (如果需要更高並行度)

#### 方法 1: 修改 .env 文件
```bash
# 編輯 .env
TASK_MAX_WORKERS=20

# 重啟 worker
docker-compose restart worker
```

#### 方法 2: 直接在 docker-compose.yml 修改
```yaml
command: celery -A app.celery_app worker --loglevel=info --concurrency=20
```

### 減少 Workers (如果記憶體不足)

```bash
# 編輯 .env
TASK_MAX_WORKERS=5

# 重啟 worker
docker-compose restart worker
```

## 最佳實踐

### Worker 數量建議

**根據 CPU 核心數**:
```
Workers = CPU 核心數 × 2 + 1
```

例如：
- 4 核心 CPU → 9 workers
- 8 核心 CPU → 17 workers
- 16 核心 CPU → 33 workers

**根據任務類型**:

1. **I/O 密集型任務** (網頁爬蟲、API 請求)
   - 可以設定較多 workers (10-20)
   - 因為大部分時間在等待網路回應

2. **CPU 密集型任務** (資料處理、圖片處理)
   - 設定較少 workers (4-8)
   - 避免 CPU 過載

3. **混合型任務**
   - 中等數量 workers (8-12)
   - 平衡 CPU 和 I/O

### 記憶體考量

**計算公式**:
```
總記憶體需求 = Worker 數量 × 每個 Worker 記憶體
```

**建議**:
- 確保系統有足夠的可用記憶體
- 留 20-30% 記憶體給系統和其他服務
- 監控記憶體使用情況

### 任務超時設定

當前配置:
```
TASK_TIMEOUT=300  # 5 分鐘
```

建議根據任務類型調整:
- 快速任務: 60-120 秒
- 一般任務: 300 秒 (當前設定)
- 長時間任務: 600-900 秒

## 監控命令

### 檢查 Worker 狀態
```bash
docker-compose exec worker celery -A app.celery_app inspect stats
```

### 檢查活躍任務
```bash
docker-compose exec worker celery -A app.celery_app inspect active
```

### 檢查已註冊的任務
```bash
docker-compose exec worker celery -A app.celery_app inspect registered
```

### 檢查 Worker 進程
```bash
docker-compose exec worker ps aux | grep celery
```

### 查看 Worker 日誌
```bash
docker-compose logs worker --tail 50 -f
```

## 效能優化

### 1. 調整 prefetch 設定
```python
# 在 celery_app.py 中
app.conf.worker_prefetch_multiplier = 1
```
- 預設值: 4
- 設為 1: 每個 worker 一次只取一個任務（更公平）
- 設為 4: 每個 worker 預取 4 個任務（更高效）

### 2. 啟用任務結果過期
```python
app.conf.result_expires = 3600  # 1 小時後過期
```

### 3. 使用任務優先級
```python
# 高優先級任務
task.apply_async(priority=9)

# 低優先級任務
task.apply_async(priority=1)
```

### 4. 限制每個 Worker 的任務數
```python
app.conf.worker_max_tasks_per_child = 1000
```
- 防止記憶體洩漏
- Worker 執行 1000 個任務後會重啟

## 故障排除

### Worker 無回應
```bash
# 重啟 worker
docker-compose restart worker

# 檢查日誌
docker-compose logs worker --tail 100
```

### 記憶體不足
```bash
# 減少 worker 數量
# 編輯 .env: TASK_MAX_WORKERS=5
docker-compose restart worker
```

### 任務堆積
```bash
# 檢查佇列長度
docker-compose exec redis redis-cli llen celery

# 清空佇列 (謹慎使用!)
docker-compose exec redis redis-cli del celery
```

### Worker 崩潰
```bash
# 檢查容器狀態
docker-compose ps worker

# 查看崩潰日誌
docker-compose logs worker --tail 200

# 重新啟動
docker-compose up -d worker
```

## 總結

### 當前狀態
- ✅ 10 個並行 Workers
- ✅ 記憶體使用正常 (~1.2-1.5 GB)
- ✅ 適合當前工作負載
- ✅ 配置合理

### 建議
- 目前的 10 個 workers 配置很好
- 如果經常有任務排隊，可以增加到 15-20
- 如果記憶體緊張，可以減少到 5-8
- 定期監控 worker 狀態和記憶體使用

### 快速調整
```bash
# 增加到 15 workers
echo "TASK_MAX_WORKERS=15" >> .env
docker-compose restart worker

# 減少到 5 workers
echo "TASK_MAX_WORKERS=5" >> .env
docker-compose restart worker
```

