#!/bin/bash

set -euo pipefail

ROLE="${SERVICE_ROLE:-api}"
PORT_VALUE="${PORT:-8000}"

case "$ROLE" in
  api)
    UVICORN_EXTRA_ARGS=""
    if [[ "${UVICORN_RELOAD:-false}" == "true" ]]; then
      UVICORN_EXTRA_ARGS="--reload"
    fi
    exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT_VALUE" $UVICORN_EXTRA_ARGS
    ;;
  worker)
    WORKER_CONCURRENCY="${TASK_MAX_WORKERS:-4}"
    WORKER_LOG_LEVEL="${LOG_LEVEL:-INFO}"
    if command -v celery >/dev/null 2>&1; then
      exec celery -A app.celery_app worker --loglevel="${WORKER_LOG_LEVEL,,}" --concurrency="$WORKER_CONCURRENCY"
    elif command -v python3 >/dev/null 2>&1; then
      exec python3 -m celery -A app.celery_app worker --loglevel="${WORKER_LOG_LEVEL,,}" --concurrency="$WORKER_CONCURRENCY"
    else
      echo "[start.sh] Celery 指令不存在，且找不到 python3" >&2
      exit 1
    fi
    ;;
  beat)
    BEAT_LOG_LEVEL="${LOG_LEVEL:-INFO}"
    if command -v celery >/dev/null 2>&1; then
      exec celery -A app.celery_app beat --loglevel="${BEAT_LOG_LEVEL,,}"
    elif command -v python3 >/dev/null 2>&1; then
      exec python3 -m celery -A app.celery_app beat --loglevel="${BEAT_LOG_LEVEL,,}"
    else
      echo "[start.sh] Celery 指令不存在，且找不到 python3" >&2
      exit 1
    fi
    ;;
  *)
    echo "[start.sh] Unknown SERVICE_ROLE '$ROLE'" >&2
    exit 1
    ;;
esac




