#!/bin/bash

# AI-Shell Web UI Startup Script

echo "=================================="
echo "AI-Shell Web UI v2.0 Startup"
echo "=================================="
echo ""

# Check if we're in the right directory
if [ ! -f "src/api/web_server.py" ]; then
    echo "Error: Please run this script from the AIShell root directory"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed. Please install Node.js 18+ from https://nodejs.org"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python is not installed. Please install Python 3.9+ from https://python.org"
    exit 1
fi

echo "Prerequisites check: ✓"
echo ""

# Install frontend dependencies if needed
if [ ! -d "web/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd web
    npm install
    cd ..
    echo "Frontend dependencies installed: ✓"
    echo ""
fi

# Check backend dependencies
echo "Checking backend dependencies..."
pip3 list | grep -q fastapi
if [ $? -ne 0 ]; then
    echo "Installing backend dependencies..."
    pip3 install -r requirements-web.txt
    echo "Backend dependencies installed: ✓"
    echo ""
fi

echo "=================================="
echo "Starting AI-Shell Web UI"
echo "=================================="
echo ""
echo "Backend API will start on: http://localhost:8000"
echo "Frontend UI will start on: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""
echo "Starting servers..."
echo ""

# Start backend in background
python3 src/api/web_server.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend
cd web
npm run dev &
FRONTEND_PID=$!

# Cleanup function
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "Servers stopped."
    exit 0
}

# Trap Ctrl+C
trap cleanup INT

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
