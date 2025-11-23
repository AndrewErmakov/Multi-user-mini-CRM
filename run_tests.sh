#!/bin/bash

set -e  # Exit on any error

echo "🧹 Cleaning up previous test services..."
docker-compose -f docker-compose.test.yml down 2>/dev/null || true
docker-compose down 2>/dev/null || true

# Чистим сети
echo "🧹 Cleaning up networks..."
docker network prune -f

# Запускаем тестовые сервисы
echo "🚀 Starting test services..."
docker-compose -f docker-compose.test.yml up -d

# Ждем пока БД будет готова
echo "⏳ Waiting for test database to be ready..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker-compose -f docker-compose.test.yml exec -T test_db pg_isready -U test_user -d test_crm_db > /dev/null 2>&1; then
        echo "✅ Test database is ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo "⏳ Waiting for test database... ($attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Test database failed to start"
    docker-compose -f docker-compose.test.yml logs test_db
    exit 1
fi

# Даем дополнительное время для полной инициализации БД
echo "⏳ Finalizing database setup..."
sleep 5

# Запускаем тесты
echo "🧪 Running tests..."
export TESTING=true
export TEST_DATABASE_URL="postgresql+asyncpg://test_user:test_password@localhost:5433/test_crm_db"
export SECRET_KEY="test-secret-key"

# Запускаем тесты с увеличенным timeout и отключением предупреждений
pytest -v --tb=short --asyncio-mode=auto -p no:warnings

# Сохраняем код выхода тестов
TEST_EXIT_CODE=$?

# Останавливаем тестовые сервисы
echo "🛑 Stopping test services..."
docker-compose -f docker-compose.test.yml down

exit $TEST_EXIT_CODE