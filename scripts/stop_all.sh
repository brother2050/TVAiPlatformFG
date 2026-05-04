#!/usr/bin/env bash
# TVAiPlatform — one-click stop all services
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "============================================"
echo "  TVAiPlatform — Stopping all services"
echo "============================================"

stop_pid() {
    local name="$1" pidfile="$2"
    if [[ -f "$pidfile" ]]; then
        local pid
        pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            echo "  ✓ $name stopped (PID $pid)"
        else
            echo "  – $name was not running (stale PID $pid)"
        fi
        rm -f "$pidfile"
    else
        echo "  – $name: no PID file found"
    fi
}

# Kill by port if PID file missing
kill_port() {
    local name="$1" port="$2"
    local pids
    pids=$(lsof -ti :"$port" 2>/dev/null || true)
    if [[ -n "$pids" ]]; then
        echo "$pids" | xargs kill -9 2>/dev/null || true
        echo "  ✓ $name killed on :$port"
    fi
}

echo "[1/5] Stopping Web dev server …"
stop_pid "Web" data/logs/web.pid
kill_port "Web" 3100

echo "[2/5] Stopping API server …"
stop_pid "API" data/logs/api.pid
kill_port "API" 8000

echo "[3/5] Stopping ChatTTS server …"
stop_pid "ChatTTS" data/logs/chattts.pid
kill_port "ChatTTS" 8090

echo "[4/5] Stopping Redis …"
if command -v redis-cli &>/dev/null; then
    redis-cli shutdown 2>/dev/null || true
    echo "  ✓ Redis stopped"
else
    echo "  – redis-cli not found, skipping"
fi

echo "[5/5] Stopping PostgreSQL …"
if command -v pg_ctlcluster &>/dev/null; then
    pg_ctlcluster 16 main stop 2>/dev/null || \
    pg_ctlcluster 17 main stop 2>/dev/null || true
    echo "  ✓ PostgreSQL stopped"
elif command -v pg_ctl &>/dev/null; then
    pg_ctl -D /var/lib/postgresql/16/main stop 2>/dev/null || \
    pg_ctl -D /var/lib/postgresql/17/main stop 2>/dev/null || true
    echo "  ✓ PostgreSQL stopped"
else
    echo "  – pg_ctl not found, skipping"
fi

# Remove temp cleanup cron
(crontab -l 2>/dev/null | grep -v cleanup_temp) | crontab - 2>/dev/null || true

echo ""
echo "============================================"
echo "  All services stopped."
echo "============================================"
