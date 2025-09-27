#!/bin/bash
set -e

echo "🚀 Fast deployment starting..."

# Configure workers
WORKERS=${WORKERS:-$([ "$ENVIRONMENT" = "production" ] && echo 4 || echo 3)}

# Virtual environment setup
VENV_PATH="/home/site/wwwroot/.venv"
if [ ! -d "$VENV_PATH" ] || [ -f "/home/site/wwwroot/.venv_corrupt" ]; then
    echo "� Creating clean venv..."
    rm -rf "$VENV_PATH" /home/site/wwwroot/.venv_corrupt
    python -m venv "$VENV_PATH"
fi
source "$VENV_PATH/bin/activate"

# Aggressive dependency installation
echo "⚡ Installing dependencies..."
pip install --upgrade pip --quiet
pip cache purge &>/dev/null || true

# Nuclear option: force reinstall everything
pip uninstall -y $(pip freeze | cut -d'=' -f1) &>/dev/null || true
pip install --force-reinstall --no-cache-dir -r requirements.txt

# Dev dependencies for non-production
[ "$ENVIRONMENT" != "production" ] && [ -f "requirements-dev.txt" ] && \
    pip install --no-cache-dir -r requirements-dev.txt

# Run migrations (fail silently)
[ -d "alembic/versions" ] && [ "$(ls -A alembic/versions 2>/dev/null)" ] && \
    alembic upgrade head &>/dev/null || echo "⚠️ Migrations skipped"

echo "🚀 Starting app with $WORKERS workers..."

# Start application
if [ "$ENVIRONMENT" = "production" ]; then
    exec gunicorn app.main:app \
        --bind=0.0.0.0:8000 \
        --workers=$WORKERS \
        --worker-class=uvicorn.workers.UvicornWorker \
        --preload \
        --max-requests=1000 \
        --timeout=30
else
    exec gunicorn app.main:app \
        --bind=0.0.0.0:8000 \
        --workers=$WORKERS \
        --worker-class=uvicorn.workers.UvicornWorker \
        --reload
fi