# 快速開始指南 (Quick Start Guide)

5 分鐘快速啟動慈濟大學招生通路自動開發系統

## 前置需求

確保已安裝以下軟體：

- ✅ Docker (20.10+)
- ✅ Docker Compose (2.0+)
- ✅ Git (2.30+)

檢查版本：
```bash
docker --version
docker-compose --version
git --version
```

## 步驟 1: 獲取程式碼

```bash
# 克隆專案
git clone <repository-url>
cd indonesia-recruitment-automation
```

## 步驟 2: 配置環境

```bash
# 複製環境變數範本
cp .env.example .env

# (可選) 編輯配置
nano .env
```

**最小配置**（使用預設值即可）：
```bash
DATABASE_URL=postgresql://user:password@db:5432/recruitment
REDIS_URL=redis://redis:6379/0
REACT_APP_API_URL=http://localhost:8000
```

## 步驟 3: 啟動服務

```bash
# 啟動所有服務（首次啟動會自動下載映像）
docker-compose up -d

# 查看服務狀態
docker-compose ps
```

預期輸出：
```
NAME                    STATUS              PORTS
recruitment-api         Up                  0.0.0.0:8000->8000/tcp
recruitment-db          Up (healthy)        0.0.0.0:5432->5432/tcp
recruitment-frontend    Up                  0.0.0.0:3000->3000/tcp
recruitment-redis       Up (healthy)        0.0.0.0:6379->6379/tcp
recruitment-worker      Up
```

## 步驟 4: 初始化資料庫

```bash
# 執行資料庫遷移
docker-compose exec api alembic upgrade head
```

## 步驟 5: 訪問應用

開啟瀏覽器訪問：

- 🌐 **前端介面**: http://localhost:3000
- 📚 **API 文件**: http://localhost:8000/docs
- ❤️ **健康檢查**: http://localhost:8000/health

## 步驟 6: 建立第一個任務

### 方法 1: 使用 Web 介面

1. 訪問 http://localhost:3000
2. 點擊左側選單「任務管理」
3. 點擊「建立新任務」
4. 填寫以下資訊：
   - 關鍵字: `SMA Internasional Jakarta`
   - 城市: `Jakarta`
   - 目標平台: 選擇全部
   - 最大結果數: `20`
5. 點擊「建立任務」
6. 點擊「啟動任務」

### 方法 2: 使用 API

```bash
# 建立任務
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "SMA Internasional Jakarta",
    "city": "Jakarta",
    "target_platforms": ["website", "facebook", "instagram"],
    "max_results": 20
  }'

# 記下返回的 task_id，然後啟動任務
curl -X POST http://localhost:8000/api/tasks/{task_id}/start
```

## 步驟 7: 查看結果

任務執行需要 5-15 分鐘，可以：

1. 在 Web 介面查看任務進度
2. 查看 Worker 日誌：
   ```bash
   docker-compose logs -f worker
   ```
3. 任務完成後，進入「資料庫」頁面查看萃取的聯絡資訊

## 常用命令

### 查看日誌

```bash
# 查看所有服務日誌
docker-compose logs -f

# 查看特定服務
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f frontend
```

### 重啟服務

```bash
# 重啟所有服務
docker-compose restart

# 重啟特定服務
docker-compose restart api
docker-compose restart worker
```

### 停止服務

```bash
# 停止所有服務
docker-compose stop

# 停止並刪除容器（保留資料）
docker-compose down

# 停止並刪除所有資料
docker-compose down -v
```

### 進入容器

```bash
# 進入 API 容器
docker-compose exec api bash

# 進入資料庫容器
docker-compose exec db psql -U user recruitment
```

## 驗證安裝

執行以下命令驗證系統正常運行：

```bash
# 檢查 API 健康狀態
curl http://localhost:8000/health

# 檢查資料庫連線
docker-compose exec api python -c "from app.database import engine; engine.connect(); print('Database OK')"

# 檢查 Redis 連線
docker-compose exec api python -c "from redis import Redis; r = Redis.from_url('redis://redis:6379/0'); r.ping(); print('Redis OK')"

# 檢查 Celery Worker
docker-compose exec worker celery -A app.celery_app inspect active
```

## 故障排除

### 問題 1: 容器無法啟動

```bash
# 查看錯誤日誌
docker-compose logs <service-name>

# 重新建立容器
docker-compose up -d --force-recreate
```

### 問題 2: 埠號衝突

如果埠號已被佔用，修改 `.env` 檔案：

```bash
API_PORT=8001
FRONTEND_PORT=3001
DB_PORT=5433
REDIS_PORT=6380
```

然後重新啟動：
```bash
docker-compose down
docker-compose up -d
```

### 問題 3: 資料庫遷移失敗

```bash
# 檢查資料庫是否運行
docker-compose exec db pg_isready -U user

# 重新執行遷移
docker-compose exec api alembic upgrade head

# 如果仍然失敗，重置資料庫
docker-compose down -v
docker-compose up -d
docker-compose exec api alembic upgrade head
```

### 問題 4: 前端無法連接 API

檢查 `.env` 中的 `REACT_APP_API_URL` 設定：

```bash
# 應該是
REACT_APP_API_URL=http://localhost:8000

# 重啟前端
docker-compose restart frontend
```

## 下一步

✅ 系統已成功啟動！

接下來可以：

1. 📖 閱讀 [使用者操作手冊](USER_MANUAL.md) 了解詳細功能
2. 🚀 查看 [部署指南](DEPLOYMENT.md) 進行生產環境部署
3. ⚙️ 參考 [環境變數說明](ENV_VARIABLES.md) 進行進階配置
4. 📋 查看 [API 文件](http://localhost:8000/docs) 了解 API 使用

## 測試資料

想要快速測試系統？使用以下關鍵字：

| 關鍵字 | 城市 | 預期結果數 |
|--------|------|-----------|
| `SMA Internasional Jakarta` | Jakarta | 20-50 |
| `Pusat Bahasa Mandarin Surabaya` | Surabaya | 10-30 |
| `Agen Pendidikan Bali` | Bali | 5-20 |

## 效能建議

### 開發環境

```bash
# .env 配置
TASK_MAX_WORKERS=2
LOG_LEVEL=DEBUG
SCRAPING_MIN_DELAY=2
SCRAPING_MAX_DELAY=5
```

### 生產環境

```bash
# .env 配置
TASK_MAX_WORKERS=8
LOG_LEVEL=WARNING
SCRAPING_MIN_DELAY=3
SCRAPING_MAX_DELAY=8
RATE_LIMIT_ENABLED=true
```

## 獲取幫助

遇到問題？

1. 📚 查看 [常見問題](USER_MANUAL.md#常見問題)
2. 🔍 搜尋 [故障排除指南](DEPLOYMENT.md#故障排除)
3. 📧 聯絡技術支援: support@example.com

---

**祝您使用愉快！** 🎉
