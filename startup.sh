#!/bin/bash
set -e

echo ">>> [startup] Instalando dependencias de sistema para WeasyPrint..."
apt-get update
apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info

echo ">>> [startup] Asegurando dependencias Python..."
cd /home/site/wwwroot
pip install --no-cache-dir -r requirements.txt

echo ">>> [startup] Lanzando gunicorn..."
: "${DJANGO_WSGI_MODULE:=app.wsgi:application}"

gunicorn --bind=0.0.0.0:${PORT:-8000} "$DJANGO_WSGI_MODULE"
