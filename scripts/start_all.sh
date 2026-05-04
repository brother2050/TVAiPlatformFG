#!/usr/bin/env bash
# TVAiPlatform — one-click start all services
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

source .env 2>/dev/null || true

# ---- Auto-create required directories ----
mkdir -p data/logs data/redis storage/media

# ---- Ensure config.yaml exists in api/ ----
if [[ -f "$PROJECT_ROOT/config.yaml" ]]; then
    cp "$PROJECT_ROOT/config.yaml" "$PROJECT_ROOT/api/config.yaml"
fi

echo "============================================"
echo "  TVAiPlatform — Starting all services"
echo "============================================"

# ---- 1. PostgreSQL ----
echo "[1/6] Starting PostgreSQL …"
if command -v pg_isready &>/dev/null && pg_isready -q 2>/dev/null; then
    echo "  ✓ PostgreSQL already running"
else
    if command -v pg_ctlcluster &>/dev/null; then
        # Try PostgreSQL 16 first (common version)
        pg_ctlcluster 16 main start 2>/dev/null || \
        pg_ctlcluster 17 main start 2>/dev/null || true
    elif command -v pg_ctl &>/dev/null; then
        pg_ctl -D /var/lib/postgresql/16/main start 2>/dev/null || \
        pg_ctl -D /var/lib/postgresql/17/main start 2>/dev/null || true
    fi
    echo "  ✓ PostgreSQL started"
fi

# ---- Setup PostgreSQL database and user ----
if command -v psql &>/dev/null; then
    PGPASSWORD=postgres psql -h localhost -U postgres -c "SELECT 1;" >/dev/null 2>&1 || true
    PGPASSWORD=postgres psql -h localhost -U postgres -c "CREATE DATABASE tvai;" >/dev/null 2>&1 || true
fi

# ---- 2. Redis ----
echo "[2/6] Starting Redis …"
if redis-cli ping &>/dev/null 2>&1; then
    echo "  ✓ Redis already running"
else
    redis-server --daemonize yes --dir ./data/redis 2>/dev/null || true
    echo "  ✓ Redis started"
fi

# ---- 3. ChatTTS server ----
echo "[3/6] Starting ChatTTS server on :8090 …"
if lsof -i :8090 &>/dev/null 2>&1; then
    echo "  ✓ ChatTTS already running on :8090"
else
    cd tts
    nohup python chattts_server.py > ../data/logs/chattts.log 2>&1 &
    echo $! > ../data/logs/chattts.pid
    cd "$PROJECT_ROOT"
    echo "  ✓ ChatTTS started (PID $(cat data/logs/chattts.pid))"
fi

# ---- 4. API server ----
echo "[4/6] Starting API server on :${API_PORT:-8000} …"
if lsof -i :"${API_PORT:-8000}" &>/dev/null 2>&1; then
    echo "  ✓ API already running on :${API_PORT:-8000}"
else
    cd api
    export PYTHONPATH="$PROJECT_ROOT"
    nohup python -m uvicorn main:app --host "${API_HOST:-0.0.0.0}" --port "${API_PORT:-8000}" \
        > ../data/logs/api.log 2>&1 &
    echo $! > ../data/logs/api.pid
    cd "$PROJECT_ROOT"
    echo "  ✓ API started (PID $(cat data/logs/api.pid))"
fi

# ---- 5. Web dev server ----
echo "[5/6] Starting Web dev server on :3100 …"
if lsof -i :3100 &>/dev/null 2>&1; then
    echo "  ✓ Web already running on :3100"
else
    cd web
    nohup pnpm dev --host 0.0.0.0 --port 3100 > ../data/logs/web.log 2>&1 &
    echo $! > ../data/logs/web.pid
    cd "$PROJECT_ROOT"
    echo "  ✓ Web started (PID $(cat data/logs/web.pid))"
fi

# ---- 6. Temp cleanup cron ----
echo "[6/6] Scheduling temp file cleanup (every 6h) …"
CRON_LINE="0 */6 * * * ${SCRIPT_DIR}/cleanup_temp.sh"
(crontab -l 2>/dev/null | grep -v cleanup_temp; echo "$CRON_LINE") | crontab - 2>/dev/null || true
echo "  ✓ Temp cleanup scheduled"

echo ""
echo "============================================"
echo "  All services started!"
echo "============================================"
echo "  API   : http://localhost:${API_PORT:-8000}"
echo "  Web   : http://localhost:3100"
echo "  ChatTTS: http://localhost:8090"
echo "  PostgreSQL: localhost:5432"
echo "  Redis : localhost:6379"
echo "============================================"
