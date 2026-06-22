#!/bin/bash
set -e

echo "==> Waiting for MySQL..."
while ! python -c "import socket; s=socket.socket(); s.connect(('db',3306)); s.close()" 2>/dev/null; do
    sleep 2
done
echo "==> MySQL is ready"

echo "==> Running migrations..."
python manage.py migrate --noinput

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Starting Gunicorn..."
exec "$@"
