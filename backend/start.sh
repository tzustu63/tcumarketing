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
    exec celery -A app.celery_app worker --loglevel="${WORKER_LOG_LEVEL,,}" --concurrency="$WORKER_CONCURRENCY"
    ;;
  beat)
    BEAT_LOG_LEVEL="${LOG_LEVEL:-INFO}"
    exec celery -A app.celery_app beat --loglevel="${BEAT_LOG_LEVEL,,}"
    ;;
  *)
    echo "[start.sh] Unknown SERVICE_ROLE '$ROLE'" >&2
    exit 1
    ;;
esac



