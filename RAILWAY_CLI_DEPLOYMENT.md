# Railway CLI 部署指南

## 當前狀態
✅ Railway CLI 已安裝 (v4.10.0)
✅ 已登入: ss248@gms.tcu.edu.tw

## 快速部署步驟

### 1. 初始化 Railway 專案

```bash
# 在專案根目錄執行
railway init
```

這會創建一個新的 Railway 專案並連結到當前目錄。

### 2. 添加資料庫服務

```bash
# 添加 PostgreSQL
railway add --database postgres

# 添加 Redis
railway add --database redis
```

Railway 會自動設定 `DATABASE_URL` 和 `REDIS_URL` 環境變數。

### 3. 創建服務配置文件

我們需要為每個服務創建配置：

#### 創建 railway.toml (根目錄)
```toml