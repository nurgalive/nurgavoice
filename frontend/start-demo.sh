#!/bin/bash

# Frontend Demo Script
# This script starts a local server for the frontend

echo "🎤 Starting NurgaVoice Frontend Demo..."

cd frontend

# Check if we're in the right directory
if [ ! -f "index.html" ]; then
    echo "❌ Error: index.html not found. Make sure you're in the nurgavoice directory."
    exit 1
fi

echo "📁 Frontend files found"
echo "🚀 Starting local server on port 3000..."
echo ""
echo "🌐 Frontend will be available at: http://localhost:3000"
echo "📝 Make sure your backend is running and accessible via ngrok"
echo ""
echo "💡 When you visit the frontend, you'll be prompted to enter your backend API URL"
echo "   Example: https://abc123.ngrok-free.app"
echo ""
echo "Press Ctrl+C to stop the server"

# Start the server
python3 -m http.server 3000 2>/dev/null || python -m http.server 3000
