#!/bin/bash

# Task Scheduler Startup Script

echo "🚀 Starting Task Scheduler..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Start backend
echo "🔧 Starting backend API..."
cd backend
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 3

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend started successfully"
else
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start frontend
echo "🖥️  Starting frontend..."
cd ../
npm start

# Cleanup on exit
trap "echo '🛑 Stopping services...'; kill $BACKEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM

wait
