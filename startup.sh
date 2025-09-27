#!/bin/bash
echo "Starting FastAPI application..."

# Always activate or create virtual environment
if [ ! -d "/home/site/wwwroot/.venv" ]; then
    echo "Creating virtual environment..."
    python -m venv /home/site/wwwroot/.venv
fi

source /home/site/wwwroot/.venv/bin/activate

# Configure workers based on environment and available resources
if [ -z "$WORKERS" ]; then
    # Auto-detect based on environment
    if [ "$ENVIRONMENT" = "production" ]; then
        WORKERS=4  # Production: more workers for better performance
    elif [ "$ENVIRONMENT" = "development" ] || [ "$ENVIRONMENT" = "dev" ]; then
        WORKERS=3  # Development: fewer workers to save resources
    else
        WORKERS=1  # Local/testing: minimal resources
    fi
fi

echo "Configured to use $WORKERS worker(s) for environment: ${ENVIRONMENT:-unknown}"

# Always update dependencies on deployment to ensure latest versions
echo "Updating dependencies..."
pip install --upgrade pip

# Check if requirements.txt has changed or force update
REQUIREMENTS_HASH_FILE="/home/site/wwwroot/.requirements_hash"
CURRENT_HASH=$(md5sum requirements.txt | cut -d' ' -f1)

if [ ! -f "$REQUIREMENTS_HASH_FILE" ] || [ "$(cat $REQUIREMENTS_HASH_FILE)" != "$CURRENT_HASH" ]; then
    echo "Requirements changed or first deployment - installing/updating all dependencies..."
    pip install --upgrade --force-reinstall --no-cache-dir -r requirements.txt
    echo "$CURRENT_HASH" > "$REQUIREMENTS_HASH_FILE"
    echo "Dependencies updated successfully!"
else
    echo "Requirements unchanged - checking for security updates..."
    pip install --upgrade --no-cache-dir -r requirements.txt
    echo "Security updates completed!"
fi

# Ejecutar migraciones de base de datos
echo "Running database migrations..."
echo "Skipping database migrations - no models defined yet..."
# alembic upgrade head

# Start the application
echo "Starting application with gunicorn using $WORKERS worker(s)..."

# Configure additional gunicorn settings based on environment
if [ "$ENVIRONMENT" = "production" ]; then
    # Production: optimized for performance and reliability
    exec gunicorn app.main:app \
        --bind=0.0.0.0:8000 \
        --workers=$WORKERS \
        --worker-class=uvicorn.workers.UvicornWorker \
        --worker-connections=1000 \
        --max-requests=1000 \
        --max-requests-jitter=100 \
        --timeout=30 \
        --keep-alive=2 \
        --preload
else
    # Development/staging: simpler configuration
    exec gunicorn app.main:app \
        --bind=0.0.0.0:8000 \
        --workers=$WORKERS \
        --worker-class=uvicorn.workers.UvicornWorker \
        --reload \
        --timeout=60
fi