#!/bin/bash
set -euxo pipefail   # e: stop on error; u: unset var = error; x: trace; o pipefail: pipeline errors

APP_DIR="/home/site/wwwroot"
VENV_DIR="$APP_DIR/.venv"

# --- 1. Virtualenv ----------------------------------------------------------
if [ ! -d "$VENV_DIR" ]; then
    echo "[INFO] Creando entorno virtual en $VENV_DIR"
    python -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

# --- 2. Instalar dependencias -----------------------------------------------
echo "[INFO] Instalando dependencias..."
pip install --upgrade pip setuptools wheel -q
pip install --no-cache-dir -r "$APP_DIR/requirements.txt" -q

# Si estás en desarrollo y tienes dev-requirements
if [ "${ENVIRONMENT:-production}" != "production" ] && [ -f "$APP_DIR/requirements-dev.txt" ]; then
    echo "[INFO] Instalando dependencias de desarrollo..."
    pip install --no-cache-dir -r "$APP_DIR/requirements-dev.txt" -q
fi

# --- 3. Migraciones CONTROLADAS (solo con tags "migrate-*") ------------------
if command -v git &>/dev/null && command -v alembic &>/dev/null; then
    # Obtener el tag exacto del commit actual
    TAG=$(git describe --tags --exact-match HEAD 2>/dev/null || echo "")
    
    if [[ "$TAG" == migrate-* ]]; then
        echo "[INFO] 🔄 Tag de migración detectado: $TAG - Ejecutando migraciones..."
        alembic upgrade head || echo "[WARN] ⚠️ Alembic falló, continuando de todos modos"
    else
        echo "[INFO] ⏭️ Sin tag de migración (tag actual: ${TAG:-'ninguno'}) - Omitiendo migraciones"
    fi
else
    echo "[INFO] ⏭️ Git o Alembic no disponible - Omitiendo migraciones"
fi

# --- 4. Lanzar Gunicorn -----------------------------------------------------
echo "[INFO] Iniciando aplicación..."
exec gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers "${WORKERS:-3}" \
    --bind 0.0.0.0:8000 \
    --timeout 120
