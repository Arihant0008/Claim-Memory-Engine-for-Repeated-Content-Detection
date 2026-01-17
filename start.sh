#!/bin/bash
# Mnemonic - Quick Start Script

echo "🚀 Starting Mnemonic..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python not found. Install Python 3.10+"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Install Node.js 18+"
    exit 1
fi

# Determine package manager
if command -v pnpm &> /dev/null; then
    PKG_MGR="pnpm"
else
    echo "⚠️  pnpm not found, using npm"
    PKG_MGR="npm"
fi

# Check .env
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env from .env.example"
        echo "⚠️  Edit .env with your API keys!"
        read -p "Press Enter after configuring .env"
    else
        echo "❌ .env.example not found!"
        exit 1
    fi
fi

# Install dependencies
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Next.js dependencies..."
    $PKG_MGR install
fi

# Start services
echo ""
echo "🔧 Starting FastAPI backend on port 8000..."
python3 api_server.py &
BACKEND_PID=$!

sleep 3

echo "🎨 Starting Next.js frontend on port 3000..."
$PKG_MGR dev &
FRONTEND_PID=$!

echo ""
echo "✅ Services started!"
echo "   Backend API:  http://localhost:8000"
echo "   Frontend UI:  http://localhost:3000"
echo "   API Docs:     http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services..."

# Wait for Ctrl+C
trap "echo ''; echo '🛑 Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo '✅ All services stopped.'; exit 0" INT
wait
