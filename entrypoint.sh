#!/bin/bash
set -e

echo "🚀 Starting FastAPI app..."

# Run DB migrations
echo "📦 Running Alembic migrations..."
alembic stamp head
alembic revision --autogenerate -m "Auto migration"
alembic upgrade head

# Start app
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
