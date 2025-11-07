# Railway Celery 連接問題故障排除

## 🔴 問題症狀

Worker 部署失敗，日誌顯示類似以下錯誤：
```
File "/usr/local/lib/python3.11/site-packages/celery/worker/consumer/consumer.py", line 469, in connect
celery.exceptions.OperationalError: Error connecting to Redis...
```

## 🎯 問題根源

**Celery Worker 無法連接到 Redis broker**，原因通常是：
1. Railway 沒有正確注入 `REDIS_URL` 環境變數
2. Worker 服務沒有連結到 Redis 資料庫
3. Redis URL 格式錯誤或無效

## ✅ 解決步驟

### 步驟 1：檢查 Redis 連結（最常見的問題）

1. 進入 Railway 專案
2. 點擊 **Worker 服務**（例如：`tcu-worker`）
3. 點擊 **Variables** 標籤
4. **檢查是否有 `REDIS_URL` 變數**

**如果沒有 `REDIS_URL`：**

5. 點擊 **+ New Variable**
6. 選擇 **Reference Variable**
7. 選擇你的 **Redis** 服務
8. 點擊 **Add**
9. 同樣方式添加 **PostgreSQL** 的連結（`DATABASE_URL`）
10. 點擊 **Deploy** 重新部署

### 步驟 2：手動設定 Redis URL（如果步驟 1 不行）

1. 進入 **Redis 服務**
2. 點擊 **Connect** 或 **Variables** 標籤
3. 找到並複製 `REDIS_URL` 的值（格式類似：`redis://default:password@host:port`）
4. 回到 **Worker 服務** → **Variables**
5. 點擊 **+ New Variable** → **Variable**
6. 添加：
   ```
   Variable Name: REDIS_URL
   Variable Value: redis://default:你的密碼@你的主機:你的端口
   ```
7. 點擊 **Add**
8. 點擊 **Deploy** 重新部署

### 步驟 3：檢查其他服務

確保以下所有服務都連結到 Redis 和 PostgreSQL：
- ✅ `tcu-api`（API 服務）
- ✅ `tcu-worker`（Worker 服務）
- ✅ `tcu-beat`（Beat 服務）

**對每個服務重複步驟 1**。

### 步驟 4：驗證部署

1. 等待 Worker 服務重新部署（約 2-5 分鐘）
2. 點擊 **Deployments** 查看最新部署
3. 點擊部署記錄查看 **Deploy Logs**
4. 確認看到類似以下成功訊息：

```
[2025-11-07 12:00:00,000: INFO/MainProcess] Connected to redis://...
[2025-11-07 12:00:00,000: INFO/MainProcess] celery@hostname ready.
```

## 🔍 進階故障排除

### 如果問題持續存在

#### 1. 檢查 Redis 服務狀態

進入 Redis 服務，確認：
- 服務狀態為 **Active**（綠色）
- 沒有錯誤訊息

#### 2. 檢查環境變數格式

確認 `REDIS_URL` 格式正確：
```
✅ 正確：redis://default:password@hostname:port
✅ 正確：redis://:password@hostname:port
❌ 錯誤：redis://hostname:port（缺少認證）
❌ 錯誤：hostname:port（缺少協議）
```

#### 3. 測試 Redis 連接

在本地測試 Redis 連接：

```bash
# 安裝 redis-cli（如果還沒有）
brew install redis  # macOS
apt install redis-tools  # Ubuntu

# 測試連接（替換為你的 Redis URL）
redis-cli -u redis://default:password@hostname:port ping

# 應該返回：PONG
```

#### 4. 檢查網絡問題

在 Railway 中：
1. 進入 Worker 服務
2. 點擊 **Settings** → **Networking**
3. 確認沒有被封鎖或限制

#### 5. 查看詳細日誌

在 Worker 服務中：
1. 點擊 **Deployments** → 最新部署
2. 點擊 **View Logs**
3. 搜尋關鍵字：`redis`、`connection`、`error`
4. 複製完整錯誤訊息

## 🚀 程式碼優化（已完成）

專案已經加入以下優化來改善 Railway 上的 Celery 連接：

```python
# backend/app/celery_app.py
celery_app.conf.update(
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=100,  # 更多重試次數
    broker_connection_timeout=30,       # 更長超時時間
    broker_heartbeat=None,              # 禁用心跳（避免連接中斷）
    broker_pool_limit=10,
    broker_transport_options={
        "visibility_timeout": 3600,
        "max_connections": 20,
        "socket_timeout": 30,
        "socket_connect_timeout": 30,
        "socket_keepalive": True,
        "health_check_interval": 25,
        "retry_on_timeout": True,
    },
)
```

這些設定可以：
- 自動重試連接（最多 100 次）
- 增加連接超時時間
- 保持連接活躍
- 在超時時自動重試

## 📋 檢查清單

完成後確認：

- [ ] Worker 服務有 `REDIS_URL` 環境變數
- [ ] Worker 服務有 `DATABASE_URL` 環境變數
- [ ] API 服務有 `REDIS_URL` 環境變數
- [ ] Beat 服務有 `REDIS_URL` 環境變數
- [ ] Redis 服務狀態為 Active
- [ ] Worker 部署成功（綠色 ✓）
- [ ] Deploy Logs 顯示 "Connected to redis://"
- [ ] Deploy Logs 顯示 "celery@hostname ready"

## 💡 預防措施

**在創建新服務時**：
1. ✅ 先創建 PostgreSQL 和 Redis
2. ✅ 創建服務後**立即**連結資料庫（在部署前）
3. ✅ 設定所有必要的環境變數
4. ✅ 然後才觸發第一次部署

這樣可以避免連接問題。

## 📞 還是無法解決？

請提供以下資訊：

1. **完整錯誤訊息**（從 Deploy Logs）
2. **環境變數截圖**（Worker 服務的 Variables 標籤）
3. **Redis URL 格式**（隱藏密碼）：
   ```
   例如：redis://default:****@region.railway.app:6379
   ```
4. **Worker 啟動命令**：
   ```bash
   celery -A app.celery_app worker --loglevel=info --concurrency=8
   ```

---

## 相關文件

- [Railway 部署設定指南](./RAILWAY_SETUP_GUIDE.md)
- [環境變數說明](./ENV_VARIABLES.md)
- [Celery 快速入門](./backend/CELERY_QUICK_START.md)

