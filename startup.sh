#!/bin/bash
set -e  # Exit on any error

echo "🚀 Starting FastAPI application deployment..."

# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================

# Determine environment-specific settings
if [ -z "$WORKERS" ]; then
    case "${ENVIRONMENT:-local}" in
        "production")
            WORKERS=4
            echo "📊 Production environment detected - using $WORKERS workers"
            ;;
        "development"|"dev")
            WORKERS=2
            echo "🛠️  Development environment detected - using $WORKERS workers"
            ;;
        *)
            WORKERS=1
            echo "🏠 Local/testing environment detected - using $WORKERS workers"
            ;;
    esac
fi

# ============================================================================
# VIRTUAL ENVIRONMENT MANAGEMENT
# ============================================================================

VENV_PATH="/home/site/wwwroot/.venv"
VENV_CORRUPT_FLAG="/home/site/wwwroot/.venv_corrupt"

# Function to create fresh virtual environment
create_venv() {
    echo "🔧 Creating fresh virtual environment..."
    rm -rf "$VENV_PATH" || true
    python -m venv "$VENV_PATH"
    source "$VENV_PATH/bin/activate"
    pip install --upgrade pip
}

# Check and setup virtual environment
if [ -f "$VENV_CORRUPT_FLAG" ] || [ ! -d "$VENV_PATH" ]; then
    create_venv
    rm -f "$VENV_CORRUPT_FLAG"
else
    source "$VENV_PATH/bin/activate"
    # Test virtual environment health
    if ! python -c "import sys; print('✅ Virtual environment is healthy')" 2>/dev/null; then
        echo "⚠️  Virtual environment appears corrupted"
        touch "$VENV_CORRUPT_FLAG"
        create_venv
        rm -f "$VENV_CORRUPT_FLAG"
    fi
fi

# ============================================================================
# DEPENDENCY MANAGEMENT
# ============================================================================

REQUIREMENTS_HASH_FILE="/home/site/wwwroot/.requirements_hash"
CURRENT_HASH=$(md5sum requirements.txt 2>/dev/null | cut -d' ' -f1 || echo "unknown")

# Function to install dependencies cleanly
install_dependencies() {
    echo "📦 Installing dependencies..."
    
    # Clean installation
    pip cache purge || true
    pip install --upgrade --force-reinstall --no-cache-dir -r requirements.txt
    
    # Install development dependencies if in non-production environment
    if [ "$ENVIRONMENT" != "production" ] && [ -f "requirements-dev.txt" ]; then
        echo "🛠️  Installing development dependencies..."
        pip install --upgrade --no-cache-dir -r requirements-dev.txt
    fi
    
    echo "$CURRENT_HASH" > "$REQUIREMENTS_HASH_FILE"
}

# Check if dependencies need update
if [ ! -f "$REQUIREMENTS_HASH_FILE" ] || [ "$(cat $REQUIREMENTS_HASH_FILE 2>/dev/null)" != "$CURRENT_HASH" ]; then
    echo "🔄 Requirements changed or first deployment"
    install_dependencies
else
    echo "✅ Requirements unchanged - checking for updates..."
    pip install --upgrade --no-cache-dir -r requirements.txt
    
    # Install/update dev dependencies if needed
    if [ "$ENVIRONMENT" != "production" ] && [ -f "requirements-dev.txt" ]; then
        pip install --upgrade --no-cache-dir -r requirements-dev.txt
    fi
fi

# ============================================================================
# DEPENDENCY VERIFICATION
# ============================================================================

echo "🔍 Verifying critical dependencies..."

# Function to verify and fix a dependency
verify_dependency() {
    local import_test="$1"
    local package_name="$2"
    local package_version="$3"
    
    if python -c "$import_test" 2>/dev/null; then
        echo "✅ $package_name is working"
        return 0
    else
        echo "❌ $package_name failed verification, reinstalling..."
        pip uninstall -y "$package_name" || true
        pip install --no-cache-dir --force-reinstall "$package_name$package_version"
        return 1
    fi
}

# Verify critical dependencies
verify_dependency "import psycopg2; print(psycopg2.__version__)" "psycopg2-binary" "==2.9.9"
verify_dependency "from websockets.datastructures import Headers" "websockets" "==12.0"
verify_dependency "import uvicorn" "uvicorn[standard]" "==0.24.0"
verify_dependency "import gunicorn" "gunicorn" "==21.2.0"

# ============================================================================
# DATABASE MIGRATIONS
# ============================================================================

echo "🗄️  Checking database migrations..."

if [ -d "alembic/versions" ] && [ "$(ls -A alembic/versions 2>/dev/null)" ]; then
    echo "📋 Migration files found, running migrations..."
    if alembic upgrade head 2>/dev/null; then
        echo "✅ Database migrations completed"
    else
        echo "⚠️  Database migrations failed - continuing startup"
        echo "💡 Check database connectivity and configuration"
    fi
else
    echo "ℹ️  No migration files found - skipping migrations"
fi

# ============================================================================
# FINAL HEALTH CHECK
# ============================================================================

echo "🏥 Final application health check..."

if python -c "
import uvicorn, gunicorn, psycopg2
from websockets.datastructures import Headers
from app.main import app
print('✅ All systems ready')
" 2>/dev/null; then
    echo "🎉 Application is ready to start!"
else
    echo "❌ Health check failed - marking environment as corrupted for next restart"
    touch "$VENV_CORRUPT_FLAG"
    echo "🚨 Application may have issues - check logs for details"
fi

# ============================================================================
# APPLICATION STARTUP
# ============================================================================

echo "🚀 Starting application with $WORKERS workers..."

# Production-optimized configuration
if [ "$ENVIRONMENT" = "production" ]; then
    exec gunicorn app.main:app \
        --bind=0.0.0.0:8000 \
        --workers=$WORKERS \
        --worker-class=uvicorn.workers.UvicornWorker \
        --worker-connections=1000 \
        --max-requests=1000 \
        --max-requests-jitter=100 \
        --timeout=30 \
        --keep-alive=2 \
        --preload \
        --access-logfile=- \
        --error-logfile=-
else
    # Development-friendly configuration
    exec gunicorn app.main:app \
        --bind=0.0.0.0:8000 \
        --workers=$WORKERS \
        --worker-class=uvicorn.workers.UvicornWorker \
        --reload \
        --timeout=60 \
        --access-logfile=- \
        --error-logfile=-
fi