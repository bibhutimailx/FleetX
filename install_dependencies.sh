#!/bin/bash

# FleetX Dependencies Installer
# This script installs all required dependencies for the demo

set -e

echo "🔧 FleetX Enhanced India Fleet Management - Dependencies Installer"
echo "=================================================================="
echo ""

# Check if we're in the right directory
if [ ! -f "backend/enhanced_india_fleet_api.py" ]; then
    echo "❌ Error: Please run this script from the FleetX root directory"
    exit 1
fi

# Check Python3 availability
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.8+ and try again."
    exit 1
fi

echo "🐍 Python3 found: $(python3 --version)"
echo ""

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd backend

# Try to use system pip first (which is what worked)
echo "   Installing FastAPI, Uvicorn, and Pydantic..."
python3 -m pip install fastapi uvicorn pydantic --user

# Verify installation
if python3 -c "import fastapi, uvicorn, pydantic" 2>/dev/null; then
    echo "   ✅ Backend dependencies installed successfully"
else
    echo "   ❌ Backend dependency installation failed"
    exit 1
fi

cd ..

echo ""
echo "🎉 All dependencies installed successfully!"
echo ""
echo "📋 Next steps:"
echo "   1. Run: ./start_demo.sh"
echo "   2. Access: http://localhost:3004"
echo ""
echo "🚛 FleetX Enhanced India Fleet Management is ready to run!"
