#!/bin/bash
set -e

# Nuclear cleanup & fresh venv
rm -rf /home/site/wwwroot/.venv /home/site/wwwroot/__pycache__ 2>/dev/null || true
python -m venv /home/site/wwwroot/.venv
source /home/site/wwwroot/.venv/bin/activate

# Silent dependency install
pip install --upgrade pip -q --disable-pip-version-check --no-warn-script-location
pip install --force-reinstall --no-cache-dir -r requirements.txt -q --no-warn-script-location
[ "$ENVIRONMENT" != "production" ] && [ -f requirements-dev.txt ] && pip install -r requirements-dev.txt -q --no-warn-script-location

# Migrations & start
alembic upgrade head &>/dev/null || true
exec gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker --workers ${WORKERS:-3} --bind 0.0.0.0:8000 --timeout 120
