#!/bin/bash
set -e

echo "=== Growth Analytics Platform: Startup ==="

# ── 1. Sheet Sync: seed & run ────────────────────────────────
# Only seed if sheets don't exist yet (persist across restarts)
if [ ! -f /app/data/sheets/S01.csv ]; then
    echo "[sheetsync] Seeding studio sheets..."
    python -m sheetsync.seed
fi

echo "[sheetsync] Running sheet sync..."
python -m sheetsync.run || echo "[sheetsync] Warning: sync issue (non-fatal)"

# ── 2. Warehouse is auto-bootstrapped by the app lifespan ────

echo "[server] Starting Growth Analytics Platform..."
echo "=========================================================="

# ── 3. Start uvicorn ─────────────────────────────────────────
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
