#!/bin/bash
# DING Setup Script

set -e

echo "🖨️  DING Setup Script"
echo "===================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python 3 is required but not found"
    exit 1
fi

# Check for cowsay
echo ""
echo "Checking for cowsay..."
if ! command -v cowsay &> /dev/null; then
    echo "⚠️  cowsay not found. Installing..."
    if command -v apt &> /dev/null; then
        sudo apt install -y cowsay
    elif command -v brew &> /dev/null; then
        brew install cowsay
    else
        echo "❌ Please install cowsay manually: sudo apt install cowsay"
        exit 1
    fi
else
    echo "✅ cowsay found"
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and configure your settings:"
    echo "   - API_KEY: Your secret API key"
    echo "   - SENDGRID_API_KEY: Your SendGrid API key"
    echo "   - SENDGRID_FROM_EMAIL: Your sender email"
    echo "   - Printer settings (if needed)"
else
    echo "✅ .env file already exists"
fi

# Initialize database
echo ""
echo "Initializing database..."
python -m core.database
echo "✅ Database initialized"

echo ""
echo "===================="
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your configuration"
echo "2. Create a user via API:"
echo "   curl -X POST http://localhost:8508/api/users \\"
echo "     -H \"Authorization: Bearer YOUR_API_KEY\" \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"username\":\"testuser\",\"email\":\"test@example.com\"}'"
echo ""
echo "3. Start the FastAPI server (Terminal 1):"
echo "   source venv/bin/activate"
echo "   uvicorn api.main:app --host 0.0.0.0 --port 8508 --reload"
echo ""
echo "4. Start the Streamlit UI (Terminal 2):"
echo "   source venv/bin/activate"
echo "   streamlit run ui/app.py --server.port 8501"
echo ""
echo "5. Open http://localhost:8501 in your browser"
echo ""
echo "Happy dinging! 🖨️✨"
