#!/bin/bash

# Kill any existing processes
echo "Stopping any existing services..."
pkill -f "uvicorn main:app"
pkill -f "vite"

# Set environment variables
export PYTHONPATH=/Users/jasonliu/dev/kura
export KURA_CHECKPOINT_DIR=/Users/jasonliu/dev/kura/tutorial_checkpoints

# Start backend
echo "Starting backend API..."
cd backend
uv run uvicorn main:app --host 0.0.0.0 --port 8001 &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 5

# Check if backend is healthy
if curl -s http://localhost:8001/api/health > /dev/null; then
    echo "✅ Backend is running!"
else
    echo "❌ Backend failed to start. Check logs."
    exit 1
fi

# Start frontend
echo "Starting frontend..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "🚀 Kura Explorer is running!"
echo "📊 Frontend: http://localhost:5173 (or http://localhost:5174 if port is in use)"
echo "🔧 API Docs: http://localhost:8001/docs"
echo ""
echo "Press Ctrl+C to stop both services"

# Handle Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT

# Wait
wait
