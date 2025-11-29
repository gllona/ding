#!/bin/bash
# Start DING Streamlit UI

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🎨 Starting DING UI..."
echo "UI will be available at: http://localhost:8501"
echo ""

source .venv/bin/activate
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"
streamlit run ui/app.py --server.port 8501
