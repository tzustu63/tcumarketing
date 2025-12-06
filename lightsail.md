# Lightsail 伺服器架構設計

## 伺服器資訊

- **IP**: 18.181.71.46
- **主域名**: harvestwize.com
- **account**: ubuntu
- **key**: /Users/kuoyuming/Desktop/程式開發/InternationalStudent /LightsailDefaultKey-ap-northeast-1.pem

## 可用網址

### 通過域名訪問（推薦）

| 服務 | 網址 | 說明 |
|------|------|------|
| **外國學生查核系統** | https://isvs.harvestwize.com | 外國學生受教權查核系統前端 |
| **外國學生查核 API** | https://isvs.harvestwize.com/api | 後端 API |
| **MinIO Console** | https://minio-isvs.harvestwize.com | 檔案儲存管理 |
| **pgAdmin** | https://pgadmin.harvestwize.com | PostgreSQL 管理工具 |
| **n8n** | https://n8n.harvestwize.com | 工作流自動化 |
| **Open WebUI** | https://webui.harvestwize.com | AI 聊天界面 |
| **Qdrant** | https://qdrant.harvestwize.com | 向量資料庫 |

### 通過 IP + 端口訪問（直接訪問）

| 服務 | 網址 | 說明 |
|------|------|------|
| 外國學生查核系統 前端 | http://18.181.71.46:3002 | 前端應用 |
| 外國學生查核系統 API | http://18.181.71.46:5003/api | 後端 API |
| 外國學生查核系統 API 文檔 | http://18.181.71.46:5003/api/docs | Swagger API 文檔 |
| 外國學生查核系統 健康檢查 | http://18.181.71.46:5003/api/health | 健康檢查端點 |
| MinIO API | http://18.181.71.46:9002 | S3 相容 API |
| MinIO Console | http://18.181.71.46:9003 | MinIO 管理界面 |
| PostgreSQL | localhost:5434 | 資料庫（僅內部） |
| Redis | localhost:6380 | 快取（僅內部） |
| pgAdmin | http://18.181.71.46:5050 | PostgreSQL 管理 |
| n8n | http://18.181.71.46:5678 | 工作流自動化 |
| Open WebUI | http://18.181.71.46:8080 | AI 聊天界面 |
| Qdrant | http://18.181.71.46:6333 | 向量資料庫 |

---

## 架構設計

### 架構圖

```
Lightsail 伺服器 (18.181.71.46)
│
├── 應用 1 (harvestwize) - 現有
│   ├── 網路: harvestwize_default (Docker Compose 預設)
│   ├── n8n: 5678 → https://n8n.harvestwize.com
│   ├── pgAdmin: 5050 → https://pgadmin.harvestwize.com
│   ├── Open WebUI: 8080 → https://webui.harvestwize.com
│   ├── PostgreSQL: 5432
│   ├── Qdrant: 6333 → https://qdrant.harvestwize.com
│   └── Nginx: 80, 443 (SSL/反向代理)
│
└── 應用 2 (ISVS - 外國學生受教權查核系統) - 新建
    ├── 網路: isvs-network (完全隔離)
    ├── 前端: 3002 → https://isvs.harvestwize.com
    ├── 後端: 5003 → https://isvs.harvestwize.com/api
    ├── PostgreSQL: 5434 → 5432 (獨立資料庫)
    ├── Redis: 6380 → 6379 (獨立快取)
    └── MinIO: 9002/9003 → 9000/9003 (獨立檔案儲存)
```

### 端口分配表

| 服務 | 應用 1 (harvestwize) | 應用 2 (ISVS) | 域名 |
|------|---------------------|---------------|------|
| 前端 | - | **3002** | isvs.harvestwize.com |
| 後端 API | - | **5003** | isvs.harvestwize.com/api |
| PostgreSQL | 5432 | **5434** | - |
| Redis | 6379 | **6380** | - |
| MinIO API | 9000 | **9002** | - |
| MinIO Console | 9001 | **9003** | minio-isvs.harvestwize.com |
| n8n | 5678 | - | n8n.harvestwize.com |
| pgAdmin | 5050 | - | pgadmin.harvestwize.com |
| Open WebUI | 8080 | - | webui.harvestwize.com |
| Qdrant | 6333 | - | qdrant.harvestwize.com |
| Nginx | 80, 443 | - | - |

### 隔離策略

1. **網路隔離**：使用不同的 Docker 網路（`harvestwize_default` vs `isvs-network`）
2. **容器隔離**：不同的容器名稱前綴（`harvestwize-*` vs `isvs-*`）
3. **資料隔離**：獨立的 Volume（`isvs_*`）
4. **資料庫隔離**：獨立的 PostgreSQL 實例（5432 vs 5434）
5. **快取隔離**：獨立的 Redis 實例（6379 vs 6380）
6. **檔案儲存隔離**：獨立的 MinIO 實例（9000/9001 vs 9002/9003）
7. **端口隔離**：不同的主機端口映射（完全避免衝突）

### 目錄結構

```
/home/ubuntu/
├── harvestwize/                    # 應用 1（現有）
│   ├── docker-compose.yml
│   └── ...
│
└── isvs/                           # 應用 2（外國學生受教權查核系統）
    ├── docker-compose.lightsail.yml  # Lightsail 專用配置
    ├── backend/                     # Node.js/Express 後端
    │   ├── src/
    │   │   ├── controllers/         # API 控制器
    │   │   ├── services/            # 業務邏輯
    │   │   ├── models/              # 資料模型
    │   │   ├── repositories/        # 資料存取層
    │   │   ├── routes/              # API 路由
    │   │   ├── middleware/          # 中間件
    │   │   └── migrations/          # 資料庫遷移
    │   ├── Dockerfile
    │   └── package.json
    ├── frontend/                    # React/Vite 前端
    │   ├── src/
    │   │   ├── components/          # React 元件
    │   │   ├── pages/               # 頁面
    │   │   ├── services/            # API 服務
    │   │   └── stores/              # 狀態管理
    │   ├── Dockerfile
    │   └── package.json
    ├── database/
    │   └── init/                    # 資料庫初始化腳本
    └── .env.production              # 獨立的環境變數
```

## 環境變數檔案範例

建立 `.env.production` 檔案（外國學生受教權查核系統）：

```env
# ============================================
# 資料庫設定
# ============================================
DB_NAME=foreign_student_verification
DB_USER=postgres
DB_PASSWORD=請修改為強密碼_至少16字元
DB_PORT=5434
PGSSLMODE=prefer

# ============================================
# Redis 設定
# ============================================
REDIS_PORT=6380
REDIS_PASSWORD=請修改為強密碼

# ============================================
# MinIO 設定（S3 相容檔案儲存）
# ============================================
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=請修改為強密碼_至少16字元
MINIO_PORT=9002
MINIO_CONSOLE_PORT=9003
AWS_S3_BUCKET=foreign-student-docs
AWS_REGION=us-east-1

# ============================================
# JWT 設定（必須修改！）
# ============================================
# 生成方式：node -e "console.log(require('crypto').randomBytes(64).toString('hex'))"
JWT_SECRET=請修改為64字元的隨機字串
JWT_EXPIRES_IN=24h
JWT_REFRESH_EXPIRES_IN=7d

# ============================================
# 應用程式設定
# ============================================
NODE_ENV=production
LOG_LEVEL=info

# ============================================
# 端口設定（避免與 harvestwize 衝突）
# ============================================
FRONTEND_PORT=3002
BACKEND_PORT=5003

# ============================================
# CORS 設定
# ============================================
CORS_ORIGIN=http://18.181.71.46:3002

# ============================================
# API URL（前端使用）
# ============================================
VITE_API_URL=http://18.181.71.46:5003/api

# ============================================
# 檔案上傳設定
# ============================================
UPLOAD_MAX_SIZE=10485760
UPLOAD_ALLOWED_TYPES=pdf,doc,docx,jpg,jpeg,png

# ============================================
# LDAP 設定（可選，用於學校帳號整合）
# ============================================
# LDAP_URL=ldap://ldap.university.edu.tw
# LDAP_BIND_DN=cn=admin,dc=university,dc=edu,dc=tw
# LDAP_BIND_PASSWORD=ldap_password
# LDAP_SEARCH_BASE=ou=users,dc=university,dc=edu,dc=tw

# ============================================
# 郵件設定（可選）
# ============================================
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=your-email@gmail.com
# SMTP_PASSWORD=your-app-password
# SMTP_FROM=noreply@university.edu.tw
```

## 端口衝突檢查

### 已使用的端口（harvestwize）
- ✅ 80, 443: Nginx (SSL/反向代理)
- ✅ 5050: pgAdmin → pgadmin.harvestwize.com
- ✅ 5432: PostgreSQL
- ✅ 5678: n8n → n8n.harvestwize.com
- ✅ 6379: Redis
- ✅ 8080: Open WebUI → webui.harvestwize.com
- ✅ 6333: Qdrant → qdrant.harvestwize.com
- ✅ 9000, 9001: MinIO（如果有的話）

### ISVS 使用的端口
- ✅ 3002: 前端 → isvs.harvestwize.com（**不衝突**）
- ✅ 5003: 後端 API → isvs.harvestwize.com/api（**不衝突**）
- ✅ 5434: PostgreSQL（**不衝突**）
- ✅ 6380: Redis（**不衝突**）
- ✅ 9002: MinIO API（**不衝突**）
- ✅ 9003: MinIO Console（**不衝突**）

## 部署步驟

### 1. 上傳專案到伺服器

```bash
# 從本地上傳
scp -i /Users/kuoyuming/Desktop/程式開發/InternationalStudent\ /LightsailDefaultKey-ap-northeast-1.pem \
  -r ./ogastudent\ har ubuntu@18.181.71.46:/home/ubuntu/isvs
```

### 2. SSH 連線到伺服器

```bash
ssh -i "/Users/kuoyuming/Desktop/程式開發/InternationalStudent /LightsailDefaultKey-ap-northeast-1.pem" \
  ubuntu@18.181.71.46
```

### 3. 設定環境變數

```bash
cd /home/ubuntu/isvs
cp .env.production.example .env.production
nano .env.production  # 修改必要的密碼和設定
```

### 4. 啟動服務

```bash
# 使用 Lightsail 專用配置啟動
docker-compose -f docker-compose.lightsail.yml --env-file .env.production up -d

# 查看服務狀態
docker-compose -f docker-compose.lightsail.yml ps
```

### 5. 初始化資料庫

```bash
# 等待資料庫啟動完成後
docker-compose -f docker-compose.lightsail.yml exec backend npm run db:migrate
```

### 6. 建立管理員帳號

```bash
# 進入後端容器
docker-compose -f docker-compose.lightsail.yml exec backend sh

# 執行建立管理員腳本
node -e "
const { Pool } = require('pg');
const bcrypt = require('bcryptjs');
const pool = new Pool();
const hash = bcrypt.hashSync('admin123', 10);
pool.query(
  'INSERT INTO users (username, password_hash, role, name) VALUES (\$1, \$2, \$3, \$4)',
  ['admin', hash, 'admin', '系統管理員']
).then(() => {
  console.log('管理員帳號建立成功');
  pool.end();
});
"
```

## 部署注意事項

1. **完全隔離**：使用獨立的 Docker 網路（`isvs-network`），不會與 harvestwize 應用有任何連接
2. **端口安全**：所有端口都經過檢查，確保不會衝突
3. **資料獨立**：使用獨立的 Volume（`isvs_*`），資料完全分離
4. **容器命名**：使用 `isvs-*` 前綴，與其他應用區分
5. **環境變數**：獨立的 `.env.production` 檔案，不會影響現有應用

## 驗證隔離

部署後可以執行以下命令驗證：

```bash
# 檢查容器
docker ps | grep isvs

# 檢查網路
docker network ls | grep isvs

# 檢查端口
ss -tulpn | grep -E ':(3002|5003|5434|6380|9002|9003)'

# 檢查 Volume
docker volume ls | grep isvs

# 測試 API 健康檢查
curl http://localhost:5003/api/health

# 測試前端
curl http://localhost:3002
```

## 服務管理指令

```bash
# 查看所有服務日誌
docker-compose -f docker-compose.lightsail.yml logs -f

# 查看特定服務日誌
docker-compose -f docker-compose.lightsail.yml logs -f backend
docker-compose -f docker-compose.lightsail.yml logs -f frontend

# 重啟服務
docker-compose -f docker-compose.lightsail.yml restart

# 停止服務
docker-compose -f docker-compose.lightsail.yml down

# 重新建置並啟動
docker-compose -f docker-compose.lightsail.yml up -d --build
```

## 資料庫備份

```bash
# 建立備份
docker-compose -f docker-compose.lightsail.yml exec -T postgres \
  pg_dump -U postgres foreign_student_verification > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢復備份
cat backup_20240103.sql | docker-compose -f docker-compose.lightsail.yml exec -T postgres \
  psql -U postgres foreign_student_verification
```

所有資源都應該完全獨立，不會與 harvestwize 應用有任何交集。
