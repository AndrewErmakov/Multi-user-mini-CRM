#!/bin/bash

set -e

echo "Running Ruff linter..."
ruff check .

echo "Running Mypy type checker..."
mypy app/ --ignore-missing-imports

echo "Running security lint with Bandit..."
bandit -c bandit.yml -r app/

echo "✅ All linters passed!"