#!/bin/bash

set -e

echo "🧹 Cleaning up previous test services..."
docker compose down 2>/dev/null || true

echo "🧹 Cleaning up networks..."
docker network prune -f

echo "🚀 Starting test services..."
docker compose up -d

echo "⏳ Waiting for test database to be ready..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker compose exec -T db pg_isready -U user -d crm_db > /dev/null 2>&1; then
        echo "✅ Test database is ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo "⏳ Waiting for test database... ($attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Test database failed to start"
    docker compose logs db
    exit 1
fi

echo "⏳ Finalizing database setup..."
sleep 5
docker compose down web

echo "🧪 Running tests..."
pytest -v --tb=short --asyncio-mode=auto -p no:warnings

TEST_EXIT_CODE=$?

echo "🛑 Stopping test services..."
docker compose down

exit $TEST_EXIT_CODE