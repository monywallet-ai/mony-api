#!/bin/bash
echo "Starting FastAPI application..."

# Instalar dependencias si es necesario
if [ ! -d "/home/site/wwwroot/.venv" ]; then
    echo "Creating virtual environment..."
    python -m venv /home/site/wwwroot/.venv
    source /home/site/wwwroot/.venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source /home/site/wwwroot/.venv/bin/activate
fi

# Ejecutar migraciones de base de datos
echo "Running database migrations..."
echo "Skipping database migrations - no models defined yet..."
# alembic upgrade head

# Iniciar la aplicación
echo "Starting application with gunicorn..."
exec gunicorn --bind=0.0.0.0:8000 --workers=4 --worker-class=uvicorn.workers.UvicornWorker app.main:app