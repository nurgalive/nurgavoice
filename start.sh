#!/bin/bash

# NurgaVoice Startup Script
# This script starts all required services for the application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting NurgaVoice Application${NC}"
echo "=================================="

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1
}

# Check prerequisites
echo -e "\n${YELLOW}📋 Checking prerequisites...${NC}"

if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

if ! command_exists redis-server && ! command_exists redis-cli; then
    echo -e "${RED}❌ Redis is not installed${NC}"
    echo "Please install Redis: sudo apt install redis-server (Ubuntu/Debian) or brew install redis (macOS)"
    exit 1
fi

if ! command_exists ffmpeg; then
    echo -e "${YELLOW}⚠️  FFmpeg is not installed. Video conversion will not work.${NC}"
    echo "Install with: sudo apt install ffmpeg (Ubuntu/Debian) or brew install ffmpeg (macOS)"
fi

echo -e "${GREEN}✅ Prerequisites check completed${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "\n${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "\n${YELLOW}🔄 Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "\n${YELLOW}📦 Installing dependencies...${NC}"
python -m pip install -r requirements.txt

# Create necessary directories
echo -e "\n${YELLOW}📁 Creating directories...${NC}"
mkdir -p uploads results models static/css static/js templates

# Check Redis
echo -e "\n${YELLOW}🔴 Checking Redis...${NC}"
if ! redis-cli ping >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Redis is not running. Starting Redis...${NC}"
    if command_exists systemctl; then
        sudo systemctl start redis-server
    elif command_exists brew; then
        brew services start redis
    else
        redis-server --daemonize yes
    fi
    
    # Wait a moment for Redis to start
    sleep 2
    
    if redis-cli ping >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Redis started successfully${NC}"
    else
        echo -e "${RED}❌ Failed to start Redis${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Redis is already running${NC}"
fi

# Start Celery worker in background
echo -e "\n${YELLOW}🔄 Starting Celery worker...${NC}"
if pgrep -f "celery.*worker" > /dev/null; then
    echo -e "${GREEN}✅ Celery worker is already running${NC}"
else
    python -m celery -A tasks.celery_app worker --loglevel=info --detach
    echo -e "${GREEN}✅ Celery worker started${NC}"
fi

# Check if port 8000 is available
if port_in_use 8000; then
    echo -e "${YELLOW}⚠️  Port 8000 is already in use${NC}"
    echo "The application might already be running or another service is using this port."
    read -p "Do you want to continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Start the FastAPI application
echo -e "\n${YELLOW}🌐 Starting FastAPI application...${NC}"
echo -e "${BLUE}📱 The application will be available at: http://localhost:8000${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the application${NC}"
echo ""

# Start the application
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}🧹 Cleaning up...${NC}"
    pkill -f "celery.*worker" 2>/dev/null || true
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Set trap to cleanup on script exit
trap cleanup EXIT
