#!/bin/bash
set -e

echo "🔄 MODO: SOLO MIGRACIONES (sin instalar dependencias)"
echo "📅 Timestamp: $(date)"

VENV_PATH="/home/site/wwwroot/.venv"
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ ERROR: No existe venv. Debe hacer deploy normal primero."
    echo "💡 Ejecute un push normal a develop antes de ejecutar migraciones."
    exit 1
fi

source "$VENV_PATH/bin/activate"

if ! command -v alembic &>/dev/null; then
    echo "❌ ERROR: Alembic no encontrado. Debe hacer deploy normal primero."
    exit 1
fi

echo "🔧 Ejecuting migrations..."
alembic upgrade head

echo "✅ Migrations successfully executed."
echo "📋 Actual status database:"
alembic current

WORKERS=${WORKERS:-3}
echo "🚀  Starting Gunicorn with $WORKERS workers..."

exec gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers $WORKERS \
    --bind 0.0.0.0:8000 \
    --timeout 120