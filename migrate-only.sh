#!/bin/bash
set -e

echo "🔄 MODO: SOLO MIGRACIONES (sin instalar dependencias)"
echo "📅 Timestamp: $(date)"

# Verificar que existe el venv (debe existir de deploy anterior)
VENV_PATH="/home/site/wwwroot/.venv"
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ ERROR: No existe venv. Debe hacer deploy normal primero."
    echo "💡 Ejecute un push normal a develop antes de ejecutar migraciones."
    exit 1
fi

# Activar venv existente
source "$VENV_PATH/bin/activate"

# Verificar que alembic está disponible
if ! command -v alembic &>/dev/null; then
    echo "❌ ERROR: Alembic no encontrado. Debe hacer deploy normal primero."
    exit 1
fi

# Ejecutar SOLO migraciones
echo "🔧 Ejecutando migraciones..."
alembic upgrade head

echo "✅ Migraciones completadas!"
echo "📋 Estado actual de la DB:"
alembic current

# Configurar workers y lanzar la aplicación (usando el venv existente)
WORKERS=${WORKERS:-3}
echo "🚀 Iniciando aplicación con migraciones aplicadas ($WORKERS workers)..."

# Launch application (usando dependencias ya instaladas)
exec gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers $WORKERS \
    --bind 0.0.0.0:8000 \
    --timeout 120