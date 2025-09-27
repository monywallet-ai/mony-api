#!/bin/bash
echo "Starting FastAPI application..."

# Always activate or create virtual environment
if [ ! -d "/home/site/wwwroot/.venv" ]; then
    echo "Creating virtual environment..."
    python -m venv /home/site/wwwroot/.venv
elif [ -f "/home/site/wwwroot/.venv_corrupt" ]; then
    echo "Previous virtual environment was corrupted, recreating..."
    rm -rf /home/site/wwwroot/.venv
    python -m venv /home/site/wwwroot/.venv
    rm -f /home/site/wwwroot/.venv_corrupt
fi

source /home/site/wwwroot/.venv/bin/activate

# Test if virtual environment is working properly
if ! python -c "import sys; print('Python virtual environment is working')" 2>/dev/null; then
    echo "Virtual environment appears corrupted, recreating..."
    touch /home/site/wwwroot/.venv_corrupt
    rm -rf /home/site/wwwroot/.venv
    python -m venv /home/site/wwwroot/.venv
    source /home/site/wwwroot/.venv/bin/activate
    rm -f /home/site/wwwroot/.venv_corrupt
fi

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
    
    # Clean problematic packages that might cause directory conflicts
    pip uninstall -y websockets || true
    pip uninstall -y psycopg2 psycopg2-binary || true
    
    # Install requirements with force reinstall
    pip install --upgrade --force-reinstall --no-cache-dir -r requirements.txt
    
    # Ensure critical packages are properly installed
    echo "Verifying critical database dependencies..."
    pip install --upgrade --force-reinstall psycopg2-binary==2.9.9
    
    echo "$CURRENT_HASH" > "$REQUIREMENTS_HASH_FILE"
    echo "Dependencies updated successfully!"
else
    echo "Requirements unchanged - checking for security updates..."
    pip install --upgrade --no-cache-dir -r requirements.txt
    
    # Always ensure psycopg2 is available for migrations
    pip install --upgrade psycopg2-binary==2.9.9
    echo "Security updates completed!"
fi

# Verify psycopg2 installation before migrations
echo "Verifying database driver installation..."
python -c "import psycopg2; print('psycopg2 is available')" || {
    echo "psycopg2 not found, attempting to install..."
    pip install --force-reinstall psycopg2-binary==2.9.9
}

# Run comprehensive dependency check
echo "Running comprehensive dependency check..."
if python check_dependencies.py; then
    echo "✅ All critical dependencies verified successfully!"
else
    echo "⚠️  Some dependencies are missing, but attempting to continue..."
fi

# Ejecutar migraciones de base de datos
echo "Running database migrations..."

# Check if we have database models defined by looking for migration files
if [ -d "alembic/versions" ] && [ "$(ls -A alembic/versions)" ]; then
    echo "Migration files found, running migrations..."
    if alembic upgrade head; then
        echo "Database migrations completed successfully!"
    else
        echo "WARNING: Database migrations failed, but continuing with application startup..."
        echo "This might be due to database connectivity issues or missing models."
        echo "Check your database connection and model definitions."
    fi
else
    echo "No migration files found - skipping database migrations."
    echo "Run 'alembic revision --autogenerate -m \"Initial migration\"' to create your first migration."
fi

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