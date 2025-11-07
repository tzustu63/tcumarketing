#!/bin/bash
# Docker 快速操作腳本
# 使用方式：./docker-quick-commands.sh [指令]

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"

require_compose() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "❌ 尚未安裝 Docker，請先安裝 Docker Desktop 或 Docker Engine。" >&2
    exit 1
  fi

  if ! command -v docker compose >/dev/null 2>&1 && ! command -v docker-compose >/dev/null 2>&1; then
    echo "❌ 未找到 docker compose 指令，請確認 Docker 安裝完整。" >&2
    exit 1
  fi
}

compose_cmd() {
  if command -v docker compose >/dev/null 2>&1; then
    docker compose -f "${COMPOSE_FILE}" "$@"
  else
    docker-compose -f "${COMPOSE_FILE}" "$@"
  fi
}

print_help() {
  cat <<'EOF'
用法：./docker-quick-commands.sh <指令>

可用指令：
  build        建置四個服務的映像檔 (api / worker / beat / frontend)
  start        啟動所有容器 (會自動建置缺少的映像檔)
  stop         停止所有容器
  restart      重新啟動所有容器
  logs <svc>   查看指定服務的日誌（svc 例如：api、worker、beat、frontend）
  shell <svc>  進入指定服務的容器 Shell
  prune        清理未使用的映像檔與容器
  help         顯示本說明
EOF
}

cmd_build() {
  echo "🚧 建置 Docker 映像檔..."
  compose_cmd build api worker beat frontend
}

cmd_start() {
  echo "🚀 啟動所有服務..."
  compose_cmd up -d
}

cmd_stop() {
  echo "🛑 停止所有服務..."
  compose_cmd down
}

cmd_restart() {
  cmd_stop
  cmd_start
}

cmd_logs() {
  local service=${1:-}
  if [[ -z "${service}" ]]; then
    echo "請指定服務名稱，例如：logs api" >&2
    exit 1
  fi
  compose_cmd logs -f "${service}"
}

cmd_shell() {
  local service=${1:-}
  if [[ -z "${service}" ]]; then
    echo "請指定服務名稱，例如：shell api" >&2
    exit 1
  fi
  compose_cmd exec "${service}" /bin/bash
}

cmd_prune() {
  echo "🧹 清理未使用的 Docker 資源..."
  docker system prune -f
}

main() {
  require_compose

  local command=${1:-help}
  shift || true

  case "${command}" in
    build) cmd_build ;;
    start) cmd_start ;;
    stop) cmd_stop ;;
    restart) cmd_restart ;;
    logs) cmd_logs "$@" ;;
    shell) cmd_shell "$@" ;;
    prune) cmd_prune ;;
    help|--help|-h) print_help ;;
    *)
      echo "未知指令: ${command}" >&2
      print_help
      exit 1
      ;;
  esac
}

main "$@"

