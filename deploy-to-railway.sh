#!/bin/bash

# Railway 自動化部署指引腳本
# 目的：協助初始化 Railway 專案、設定環境變數與部署服務

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAILWAY_ENVIRONMENT="${RAILWAY_ENVIRONMENT:-production}"

print_section() {
  echo "\n========================================"
  echo "$1"
  echo "========================================"
}

require_cli() {
  if ! command -v railway >/dev/null 2>&1; then
    echo "[ERROR] 尚未安裝 Railway CLI。請先執行：npm install -g @railway/cli" >&2
    exit 1
  fi
}

ensure_login() {
  if ! railway whoami >/dev/null 2>&1; then
    echo "[ERROR] 尚未登入 Railway。請先執行：railway login" >&2
    exit 1
  fi
}

ensure_project() {
  print_section "檢查或建立 Railway 專案"
  if ! railway status >/dev/null 2>&1; then
    echo "尚未綁定專案。請先手動執行 'railway init' 以選擇工作區與專案後再重新執行本腳本。" >&2
    exit 1
  fi
  railway status
}

ensure_environment() {
  print_section "切換或建立環境 ($RAILWAY_ENVIRONMENT)"
  if ! railway environment "$RAILWAY_ENVIRONMENT" >/dev/null 2>&1; then
    echo "環境不存在，建立新環境: $RAILWAY_ENVIRONMENT"
    railway environment "$RAILWAY_ENVIRONMENT" new
  fi
  railway environment "$RAILWAY_ENVIRONMENT"
}

ensure_resources() {
  print_section "檢查資料庫與 Redis 資源"
  if railway resources >/dev/null 2>&1; then
    echo "現有資源列表："
    railway resources
  else
    echo "目前 Railway CLI 不支援在腳本內列出/建立資源。請確認已於 Railway 控制台建立 PostgreSQL 與 Redis 資源後再繼續。"
  fi
}

show_manual_steps() {
  print_section "後續手動步驟"
  cat <<'EOF'
1. 建立服務與部署程式碼
   - 推薦在 Railway 控制台依序建立以下服務：tcu-api、tcu-worker、tcu-beat、tcu-frontend。
   - 若偏好 CLI，可分別切換到 `backend/`、`frontend/` 目錄執行 `railway up`，並在部署後於控制台重新命名服務。

2. 設定環境變數
   - 使用 `railway variables --service <服務名稱> --environment production` 進入互動式界面，設定：
       GOOGLE_API_KEY
       GOOGLE_CSE_ID
       SERVICE_ROLE（分別為 api / worker / beat）
       UVICORN_RELOAD、PORT、TASK_MAX_WORKERS、REACT_APP_API_URL 等其他必要值

3. 確認資料庫與 Redis
   - 在 Railway 控制台的 Resources 區塊建立 PostgreSQL 與 Redis，並連結到專案。
   - 服務中可直接使用自動注入的 `DATABASE_URL`、`REDIS_URL`。

4. 執行資料庫遷移
   - `railway run --service tcu-api alembic upgrade head`

5. 驗證服務
   - 在專案控制台檢查各服務的 Deployments、Logs。
   - 造訪前端與 API URL，確認是否可正常運作。

完成上述步驟後，即完成 Railway 部署。若需更多細節，請參考 `RAILWAY_DEPLOYMENT.md`。
EOF
}

main() {
  print_section "Railway 自動化部署"
  require_cli
  ensure_login
  ensure_project
  ensure_environment
  ensure_resources
  show_manual_steps
}

main "$@"

