# 慈濟大學招生通路自動開發系統

Tzu Chi University Recruitment Automation System - 自動化網頁爬蟲與聯絡資訊萃取系統

## 專案簡介

本系統旨在取代傳統的人工市場調查流程，能夠 7x24 小時不間斷地在 Google、Facebook、Instagram 上搜尋潛在合作夥伴，自動萃取聯絡資訊，並建立結構化的資料庫。

### 核心功能

- 🔍 **自動搜尋** - 在 Google 上自動搜尋目標機構
- 🤖 **AI 萃取** - 使用 NLP 技術萃取 Email 和 WhatsApp 號碼
- 📊 **資料管理** - 結構化儲存和管理聯絡資訊
- 📤 **資料匯出** - 支援 Excel 格式匯出
- ⏰ **自動化執行** - 7x24 小時背景任務執行
- 📈 **監控儀表板** - 即時查看系統狀態和統計資料
- 🚦 **智能限流** - 多層級速率限制，保護目標網站不被過度請求
- 🎯 **任務優先級** - 智能任務調度，確保關鍵任務優先執行

## 技術架構

### 後端
- **Python 3.11+**
- **FastAPI** - REST API 框架
- **Celery** - 分散式任務佇列
- **PostgreSQL** - 主要資料庫
- **Redis** - 訊息佇列和快取
- **Selenium/Playwright** - 網頁爬蟲
- **SQLAlchemy** - ORM

### 前端
- **React 18**
- **Tailwind CSS**
- **Axios** - HTTP 客戶端

## 快速開始

### 5 分鐘快速啟動

```bash
# 1. 克隆專案
git clone <repository-url>
cd indonesia-recruitment-automation

# 2. 配置環境
cp .env.example .env

# 3. 啟動服務
docker-compose up -d

# 4. 初始化資料庫
docker-compose exec api alembic upgrade head

# 5. 訪問應用
# 前端: http://localhost:3000
# API 文件: http://localhost:8000/docs
```

📖 **詳細步驟請參考** [快速開始指南](QUICK_START.md)

### 前置需求

- Docker 20.10+
- Docker Compose 2.0+
- Git 2.30+

**本地開發額外需求**:
- Python 3.11+
- Node.js 18+

### 本地開發

#### 後端開發

1. 建立虛擬環境：
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. 安裝依賴：
```bash
pip install -r requirements.txt
```

3. 啟動資料庫和 Redis：
```bash
docker-compose up -d db redis
```

4. 執行資料庫遷移：
```bash
alembic upgrade head
```

5. 啟動 API 服務：
```bash
uvicorn app.main:app --reload
```

6. 啟動 Celery Worker：
```bash
celery -A app.celery_app worker --loglevel=info
```

#### 前端開發

1. 安裝依賴：
```bash
cd frontend
npm install
```

2. 啟動開發伺服器：
```bash
npm start
```

## 專案結構

```
.
├── backend/                 # 後端應用
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py         # FastAPI 應用入口
│   │   ├── config.py       # 配置管理
│   │   ├── celery_app.py   # Celery 配置
│   │   ├── models/         # 資料庫模型
│   │   ├── repositories/   # 資料存取層
│   │   ├── services/       # 業務邏輯層
│   │   ├── api/            # API 路由
│   │   ├── tasks/          # Celery 任務
│   │   ├── scraper/        # 爬蟲引擎
│   │   └── extractor/      # 資訊萃取模組
│   ├── alembic/            # 資料庫遷移
│   ├── tests/              # 測試
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # 前端應用
│   ├── public/
│   ├── src/
│   │   ├── components/    # React 元件
│   │   ├── pages/         # 頁面
│   │   ├── services/      # API 服務
│   │   └── utils/         # 工具函數
│   ├── package.json
│   └── Dockerfile
├── .kiro/                 # Kiro Spec 文件
│   └── specs/
│       └── indonesia-recruitment-automation/
│           ├── requirements.md
│           ├── design.md
│           └── tasks.md
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## API 文件

啟動服務後，訪問 http://localhost:8000/docs 查看完整的 API 文件（Swagger UI）。

### 主要 API 端點

- `POST /api/tasks` - 建立新任務
- `GET /api/tasks` - 獲取任務列表
- `GET /api/tasks/{id}` - 獲取任務詳情
- `POST /api/tasks/{id}/start` - 啟動任務
- `GET /api/contacts` - 查詢聯絡資訊
- `POST /api/contacts/export` - 匯出資料
- `GET /api/stats` - 獲取統計資料

## 環境變數

查看 `.env.example` 檔案了解所有可配置的環境變數。

### 速率限制配置

系統實現了多層級的速率限制機制，確保不會過度請求目標網站：

```bash
# 啟用速率限制
RATE_LIMIT_ENABLED=true

# 每個域名的請求限制（預設：10 次/60 秒）
RATE_LIMIT_MAX_REQUESTS_PER_DOMAIN=10
RATE_LIMIT_DOMAIN_TIME_WINDOW=60

# 最小請求間隔（預設：2 秒）
RATE_LIMIT_MIN_REQUEST_INTERVAL=2.0

# 全域請求限制（預設：60 次/分鐘）
RATE_LIMIT_MAX_REQUESTS_PER_MINUTE=60
RATE_LIMIT_MAX_CONCURRENT_REQUESTS=10

# 任務優先級管理
TASK_PRIORITY_ENABLED=true
```

詳細說明請參考 [backend/RATE_LIMITING_IMPLEMENTATION.md](backend/RATE_LIMITING_IMPLEMENTATION.md)

## 測試

### 後端測試

```bash
cd backend
pytest
```

### 前端測試

```bash
cd frontend
npm test
```

## 部署

### 開發環境部署

詳細步驟請參考 [DEPLOYMENT.md](DEPLOYMENT.md)

```bash
# 1. 複製環境變數
cp .env.example .env

# 2. 啟動所有服務
docker-compose up -d

# 3. 初始化資料庫
docker-compose exec api alembic upgrade head

# 4. 訪問應用
# 前端: http://localhost:3000
# API: http://localhost:8000/docs
```

### 生產環境部署

```bash
# 1. 準備生產環境配置
cp .env.example .env.production
nano .env.production

# 2. 使用生產配置啟動
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 3. 配置 Nginx 反向代理（可選）
# 4. 設定 SSL/TLS 憑證
```

完整部署指南請參考 [DEPLOYMENT.md](DEPLOYMENT.md)

## 文件

- 📖 [使用者操作手冊](USER_MANUAL.md) - 完整的功能說明和使用指南
- 🚀 [部署指南](DEPLOYMENT.md) - 開發和生產環境部署說明
- 📋 [需求文件](.kiro/specs/indonesia-recruitment-automation/requirements.md) - 系統需求規格
- 🎨 [設計文件](.kiro/specs/indonesia-recruitment-automation/design.md) - 系統架構和設計
- ✅ [實作計畫](.kiro/specs/indonesia-recruitment-automation/tasks.md) - 開發任務清單
- 🚦 [速率限制說明](backend/RATE_LIMITING_IMPLEMENTATION.md) - 速率限制機制
- 🔄 [工作流程整合](backend/WORKFLOW_INTEGRATION_DIAGRAM.md) - 系統工作流程

## 維護與監控

### 查看日誌

```bash
# 查看所有服務日誌
docker-compose logs -f

# 查看特定服務
docker-compose logs -f api
docker-compose logs -f worker
```

### 監控系統狀態

```bash
# 查看容器狀態
docker-compose ps

# 查看資源使用
docker stats

# 查看資料庫大小
docker-compose exec db psql -U user -d recruitment -c "SELECT pg_size_pretty(pg_database_size('recruitment'));"
```

### 備份資料庫

```bash
# 建立備份
docker-compose exec -T db pg_dump -U user recruitment > backup_$(date +%Y%m%d).sql

# 恢復備份
cat backup_20240103.sql | docker-compose exec -T db psql -U user recruitment
```

## 故障排除

### 常見問題

**容器無法啟動**
```bash
docker-compose logs <service-name>
docker-compose up -d --force-recreate <service-name>
```

**資料庫連線失敗**
```bash
docker-compose exec db pg_isready -U user
docker-compose restart db
```

**Worker 無法處理任務**
```bash
docker-compose logs -f worker
docker-compose restart worker
```

更多故障排除資訊請參考 [DEPLOYMENT.md](DEPLOYMENT.md#故障排除)

## 效能優化

### 調整 Worker 數量

```bash
# 在 .env 中設定
TASK_MAX_WORKERS=8

# 或使用 docker-compose scale
docker-compose up -d --scale worker=4
```

### 資料庫優化

```sql
-- 定期執行
ANALYZE;
REINDEX DATABASE recruitment;
VACUUM;
```

## 安全建議

1. ✅ 使用強密碼（資料庫、Redis）
2. ✅ 啟用 SSL/TLS（生產環境）
3. ✅ 限制網路存取（防火牆規則）
4. ✅ 定期更新依賴套件
5. ✅ 定期備份資料
6. ✅ 監控系統日誌
7. ✅ 使用最小權限原則

## 貢獻指南

本專案目前為內部專案，如需貢獻請聯絡開發團隊。

## 授權

本專案為私有專案，未經授權不得使用。

## 聯絡方式

- 📧 技術支援: support@example.com
- 📚 文件問題: docs@example.com
- 🐛 Bug 回報: 請使用 Issue Tracker

## 版本歷史

### v1.0.0 (2024-01-03)
- ✨ 初始版本發布
- 🔍 Google 搜尋爬取功能
- 🤖 AI 聯絡資訊萃取
- 📊 資料管理和匯出
- 🚦 速率限制機制
- 📈 監控儀表板

---

**開發團隊** | **最後更新**: 2024-01-03
