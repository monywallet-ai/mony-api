#!/bin/bash
echo "Starting FastAPI application..."

# Always activate or create virtual environment    # - name: Setup Python
    #   uses: actions/setup-python@v5
    #   with:
    #     python-version: '3.12'
        
    # - name: Install dependencies
    #   run: |
    #     python -m pip install --upgrade pip
    #     pip install -r requirements.txt
if [ ! -d "/home/site/wwwroot/.venv" ]; then
    echo "Creating virtual environment..."
    python -m venv /home/site/wwwroot/.venv
fi

source /home/site/wwwroot/.venv/bin/activate

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

# Iniciar la aplicación
echo "Starting application with gunicorn..."
exec gunicorn --bind=0.0.0.0:8000 --workers=4 --worker-class=uvicorn.workers.UvicornWorker app.main:app