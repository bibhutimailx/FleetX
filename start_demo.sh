#!/bin/bash

# FleetX Enhanced India Demo - Quick Start Script
# This script starts both backend and frontend for localhost:3004 access

set -e

echo "🇮🇳 FleetX Enhanced India Fleet Management - Demo Startup"
echo "========================================================"
echo ""

# Check if we're in the right directory
if [ ! -f "backend/enhanced_india_fleet_api.py" ]; then
    echo "❌ Error: Please run this script from the FleetX root directory"
    echo "   Current directory: $(pwd)"
    echo "   Expected files: backend/enhanced_india_fleet_api.py"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "backend/venv" ]; then
    echo "🐍 Activating Python virtual environment..."
    source backend/venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️  No virtual environment found. Make sure you have the required Python packages installed."
fi

# Function to kill processes on script exit
cleanup() {
    echo ""
    echo "🛑 Shutting down FleetX demo..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo "   ✅ Backend API stopped"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo "   ✅ Frontend server stopped"
    fi
    echo "👋 FleetX demo stopped. Thank you!"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo ""
echo "🚀 Starting FleetX Enhanced India Backend API on port 8006..."
cd backend
python enhanced_india_fleet_api.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 5

# Check if backend is running
if kill -0 $BACKEND_PID 2>/dev/null; then
    echo "✅ Backend API started successfully"
else
    echo "❌ Backend failed to start"
    exit 1
fi

echo ""
echo "🌐 Starting FleetX Enhanced India Frontend on port 3004..."
cd frontend
python serve_enhanced_india.py &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
echo "⏳ Waiting for frontend to initialize..."
sleep 3

# Check if frontend is running
if kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "✅ Frontend server started successfully"
else
    echo "❌ Frontend failed to start"
    cleanup
fi

echo ""
echo "🎉 FleetX Enhanced India Fleet Management is now running!"
echo ""
echo "📍 Access URLs:"
echo "   🌐 Main Application: http://localhost:3004"
echo "   📊 API Documentation: http://localhost:8006/docs"
echo "   🏥 Health Check: http://localhost:8006/health"
echo ""
echo "🚛 Fleet Details:"
echo "   • 13 Heavy Coal Transport Trucks (OD-03-NT-1001 to 1013)"
echo "   • Route: NTPC Talcher → Chandilkhol, Odisha, India"
echo "   • Real-time tracking with 8-second updates"
echo "   • PagerDuty-style escalation system"
echo "   • AI-powered smart gate monitoring"
echo ""
echo "⌨️  Press Ctrl+C to stop both services"
echo ""

# Keep script running and show logs
echo "📋 Live System Status:"
while true; do
    sleep 10
    
    # Check if processes are still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "❌ Backend process died unexpectedly"
        cleanup
    fi
    
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "❌ Frontend process died unexpectedly"
        cleanup
    fi
    
    echo "✅ $(date '+%H:%M:%S') - Both services running normally"
done
