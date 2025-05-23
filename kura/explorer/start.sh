#!/bin/bash

# Start the backend API in the background
echo "Starting Kura Explorer Backend..."
cd backend
python3 -m uvicorn main:app --reload --port 8001 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 2

# Start the frontend
echo "Starting Kura Explorer Frontend..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "🚀 Kura Explorer is running!"
echo "📊 Frontend: http://localhost:5173"
echo "🔧 API Docs: http://localhost:8001/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait