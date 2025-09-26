#!/bin/sh
set -e

echo "Starting FastAPI application..."

# Set default values for environment variables
export WORKERS=${WORKERS:-4}
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-8000}

# Health check
echo "Environment ready, virtual environment is already configured"

# Execute database migrations when ready
echo "Skipping database migrations - no models defined yet..."
# alembic upgrade head

# Detect OS and choose appropriate server
if [ "$(uname -s)" = "Linux" ] || [ "$(uname -s)" = "Darwin" ]; then
    # Unix-like systems: use gunicorn
    echo "Starting application with gunicorn on ${HOST}:${PORT} with ${WORKERS} workers..."
    exec uv run gunicorn app.main:app \
        -w "$WORKERS" \
        -k uvicorn.workers.UvicornWorker \
        --bind "${HOST}:${PORT}" \
        --access-logfile - \
        --error-logfile - \
        --max-requests 1000 \
        --max-requests-jitter 100 \
        --preload
else
    # Windows: use uvicorn directly (gunicorn doesn't work on Windows)
    echo "Starting application with uvicorn on ${HOST}:${PORT} (Windows detected)..."
    exec uv run uvicorn app.main:app \
        --host "$HOST" \
        --port "$PORT" \
        --access-log \
        --log-level info
fi