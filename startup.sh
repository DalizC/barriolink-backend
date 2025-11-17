#!/bin/bash
set -e

echo "[startup] Instalando dependencias nativas para WeasyPrint..."

apt-get update
apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info

echo "[startup] Dependencias instaladas correctamente. Devolviendo control al contenedor."

# Importante: NO arrancamos gunicorn aquí.
# App Service, después de ejecutar este script, sigue con su proceso normal:
# detecta Django y ejecuta algo como:
#   gunicorn --bind=0.0.0.0 --timeout 600 <module>.wsgi
