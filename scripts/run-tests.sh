#!/bin/bash
# run-tests.sh - Run full test suite with coverage
# Usage: ./scripts/run-tests.sh [options]
#
# Options:
#   --unit        Run only unit tests
#   --api         Run only API tests
#   --integration Run only integration tests
#   --coverage    Include coverage report (default: on)
#   --no-coverage Skip coverage report
#   --verbose     Verbose output

set -e

cd "$(dirname "$0")/../backend"

echo "========================================="
echo "  Running Tests"
echo "========================================="
echo ""

# Default options
COVERAGE="--cov=app --cov-report=term-missing"
VERBOSE="-v"
TEST_PATH="tests/"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            TEST_PATH="tests/unit/"
            shift
            ;;
        --api)
            TEST_PATH="tests/api/"
            shift
            ;;
        --integration)
            TEST_PATH="tests/integration/"
            shift
            ;;
        --coverage)
            COVERAGE="--cov=app --cov-report=term-missing"
            shift
            ;;
        --no-coverage)
            COVERAGE=""
            shift
            ;;
        --verbose)
            VERBOSE="-vv"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--unit|--api|--integration] [--coverage|--no-coverage] [--verbose]"
            exit 1
            ;;
    esac
done

echo "Test path: $TEST_PATH"
echo "Coverage: ${COVERAGE:-disabled}"
echo ""

# Run tests
uv run pytest $TEST_PATH $VERBOSE $COVERAGE

echo ""
echo "========================================="
echo "  Tests Complete"
echo "========================================="
