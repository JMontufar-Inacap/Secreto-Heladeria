#!/usr/bin/env bash
# Abort on errors
set -o errexit

# Instalar dependencias
pip install -r requirements.txt

# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Ejecutar migraciones
python manage.py migrate --noinput
