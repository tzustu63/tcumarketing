# 部署完成報告

## 部署資訊

**部署時間**: 2025-11-04
**平台**: DigitalOcean
**地區**: Singapore (sgp1)

## 伺服器資訊

- **IP 地址**: 188.166.228.79
- **規格**: 2 vCPU, 2GB RAM, 50GB SSD
- **作業系統**: Ubuntu 22.04 LTS

## 服務狀態

所有服務已成功部署並運行：

### 1. 資料庫 (PostgreSQL)
- **狀態**: ✅ 運行中 (healthy)
- **端口**: 5433 (外部) → 5432 (內部)

### 2. Redis
- **狀態**: ✅ 運行中 (healthy)
- **端口**: 6379

### 3. API 服務
- **狀態**: ✅ 運行中
- **端口**: 8000
- **健康檢查**: http://188.166.228.79:8000/health
- **回應**: `{"status":"healthy"}`

### 4. Worker 服務
- **狀態**: ✅ 運行中
- **功能**: 處理爬蟲任務

### 5. Beat 服務
- **狀態**: ✅ 運行中
- **功能**: 定時任務調度

### 6. 前端服務
- **狀態**: ✅ 運行中
- **端口**: 3000
- **訪問**: http://188.166.228.79:3000

## 訪問方式

### 前端界面
```
http://188.166.228.79:3000
```

### API 端點
```
http://188.166.228.79:8000
```

### API 文檔
```
http://188.166.228.79:8000/docs
```

## 管理命令

### SSH 連接
```bash
ssh root@188.166.228.79
```

### 查看服務狀態
```bash
cd /root/tcu-recruitment-system
docker-compose ps
```

### 查看日誌
```bash
# 查看所有服務日誌
docker-compose logs -f

# 查看特定服務日誌
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
docker-compose down
```

### 啟動服務
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 運行資料庫遷移（首次部署必須）
```bash
docker-compose exec api alembic upgrade head
```

## 環境變數

環境變數已配置在 `.env` 文件中，包括：
- 資料庫連接資訊
- Redis 連接資訊
- API 配置
- Google API 金鑰

## CORS 問題已修復

前端已配置為使用正確的 API URL (`http://188.166.228.79:8000`)，CORS 問題已解決。

如果您需要更改 API URL（例如使用域名），請：
1. 修改 `docker-compose.prod.yml` 中的 `REACT_APP_API_URL` 構建參數
2. 重新構建前端：
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache frontend
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d frontend
```

## 下一步建議

### 1. 設定域名（可選）
如果您有域名，可以：
1. 將域名 A 記錄指向 `188.166.228.79`
2. 設定 Nginx 反向代理
3. 配置 SSL 證書（Let's Encrypt）

### 2. 設定防火牆
```bash
# 只允許必要的端口
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 3000/tcp  # Frontend
ufw allow 8000/tcp  # API
ufw enable
```

### 3. 設定自動備份
建議定期備份：
- PostgreSQL 資料庫
- 導出的 Excel 文件
- 日誌文件

### 4. 監控設定
考慮設定：
- 服務健康監控
- 磁碟空間監控
- 記憶體使用監控

## 故障排除

### 如果服務無法啟動
```bash
# 查看詳細日誌
docker-compose logs

# 重新構建並啟動
docker-compose down
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### 如果資料庫連接失敗
```bash
# 檢查資料庫狀態
docker-compose exec db psql -U recruitment_user -d recruitment_db -c "SELECT 1;"
```

### 如果 Worker 無法處理任務
```bash
# 檢查 Redis 連接
docker-compose exec redis redis-cli ping

# 重啟 Worker
docker-compose restart worker
```

## 成本估算

- **Droplet 費用**: $18/月 (2GB RAM)
- **流量**: 2TB/月（包含在內）
- **備份**: $3.60/月（可選，20% Droplet 費用）

## 支援

如有問題，請檢查：
1. 服務日誌：`docker-compose logs -f`
2. 系統資源：`htop` 或 `docker stats`
3. 磁碟空間：`df -h`

---

**部署完成！** 🎉

系統已成功部署並運行在 DigitalOcean 上。
