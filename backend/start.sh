#!/bin/bash

# NurgaVoice Backend Startup Script
# This script starts the backend services required for NurgaVoice

set -e

echo "🎤 Starting NurgaVoice Backend Services..."

# Check if Redis is running
if ! pgrep -x "redis-server" > /dev/null; then
    echo "⚠️  Redis not running. Please start Redis first:"
    echo "   sudo systemctl start redis-server"
    echo "   # OR"
    echo "   docker run -d -p 6379:6379 redis:alpine"
    exit 1
fi

echo "✅ Redis is running"

# Check if virtual environment is activated
if [[ -z "${VIRTUAL_ENV}" ]]; then
    echo "⚠️  Virtual environment not detected. Consider activating one:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
fi

# Install dependencies if needed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Start Celery worker in background
echo "🚀 Starting Celery worker..."
celery -A tasks worker --loglevel=info --detach

# Wait a moment for Celery to start
sleep 2

# Start the FastAPI backend
echo "🚀 Starting FastAPI backend on port 8000..."
echo "📝 API will be available at: http://localhost:8000"
echo "📝 API documentation: http://localhost:8000/docs"
echo ""
echo "🌐 To expose via ngrok, run in another terminal:"
echo "   ngrok http 8000"
echo ""
echo "Press Ctrl+C to stop all services"

# Trap SIGINT to cleanup
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    pkill -f "celery.*worker" || true
    echo "✅ Services stopped"
    exit 0
}

trap cleanup SIGINT

# Start the backend
python backend.py
