#!/bin/bash

# Test runner script for Interior AI Service
# Usage: ./run_tests.sh [test_type] [options]

set -e

# Default values
TEST_TYPE=${1:-"unit"}
VERBOSE=${2:-"-v"}
COVERAGE=${3:-"--cov"}

echo "🧪 Running $TEST_TYPE tests for Interior AI Service..."

case $TEST_TYPE in
    "unit")
        echo "📋 Running unit tests..."
        uv run pytest tests/unit/ $VERBOSE $COVERAGE
        ;;
    "integration")
        echo "🔗 Running integration tests..."
        uv run pytest tests/integration/ $VERBOSE $COVERAGE
        ;;
    "e2e")
        echo "🌐 Running end-to-end tests..."
        uv run pytest tests/e2e/ $VERBOSE $COVERAGE
        ;;
    "all")
        echo "🎯 Running all tests..."
        uv run pytest tests/ $VERBOSE $COVERAGE
        ;;
    "quick")
        echo "⚡ Running quick tests (no coverage)..."
        uv run pytest tests/unit/ $VERBOSE --no-cov
        ;;
    "coverage")
        echo "📊 Running tests with coverage report..."
        uv run pytest tests/ $VERBOSE --cov=app --cov-report=html --cov-report=term-missing
        ;;
    *)
        echo "❌ Unknown test type: $TEST_TYPE"
        echo "Available options: unit, integration, e2e, all, quick, coverage"
        exit 1
        ;;
esac

echo "✅ Tests completed!" 