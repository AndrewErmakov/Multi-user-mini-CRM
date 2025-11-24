#!/bin/bash

echo "Running database migrations..."

# Apply migrations
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "Migrations applied successfully"
else
    echo "Failed to apply migrations"
    exit 1
fi