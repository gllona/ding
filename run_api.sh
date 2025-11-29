#!/bin/bash
# Start DING FastAPI server

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 Starting DING API server..."
echo "API will be available at: http://localhost:8508"
echo "API Docs: http://localhost:8508/docs"
echo ""

source .venv/bin/activate
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"
uvicorn api.main:app --host 0.0.0.0 --port 8508 --reload
