#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "==> 📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> 🎨 Collecting static files for WhiteNoise..."
python manage.py collectstatic --no-input

echo "==> 🚀 Running database migrations..."
python manage.py migrate

echo "==> Creating cache table..."
python manage.py createcachetable

echo "==> ✅ Build completed successfully!"