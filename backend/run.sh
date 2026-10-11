#!/bin/bash

# Home Services Platform - Backend Startup Script
# Run this to start the server: bash run.sh

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   Home Services Lead Capture Agent - Starting...              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check Python
echo "✓ Checking Python..."
python3 --version

# Check virtual environment
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating..."
    python3 -m venv venv
fi

echo "✓ Activating virtual environment..."
source venv/bin/activate

# Check dependencies
echo "✓ Checking dependencies..."
if ! python -c "import fastapi" 2>/dev/null; then
    echo "⚠️  Dependencies missing. Installing..."
    pip install -r requirements.txt -q
fi

# Check .env
if [ ! -f ".env" ]; then
    echo "⚠️  .env file missing. Creating from template..."
    cp .env.example .env
    echo "   Please edit .env and add your API keys!"
    echo ""
fi

# Display info
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   Starting Server on http://localhost:8000                    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📍 Health check:"
echo "   curl http://localhost:8000/health"
echo ""
echo "🧪 Test the agent:"
echo "   curl -X POST http://localhost:8000/api/test/transcript \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"transcript\": \"I have an emergency. Toilet overflowing.\"}'"
echo ""
echo "Stop with: Ctrl+C"
echo ""

# Run the app
python main.py
