#!/bin/bash

# Development script for Kura Explorer with hot reloading
echo "🚀 Starting Kura Explorer in development mode with hot reloading..."

# Stop any existing containers
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

# Build and start services
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

echo "✅ Development environment is running!"
echo "📱 Frontend: http://localhost:5173"
echo "🔧 Backend API: http://localhost:8001"
echo "📋 Full app via proxy: http://localhost:8080 (if nginx profile is enabled)"
echo ""
echo "💡 File changes will automatically trigger rebuilds!"
echo "🛑 Press Ctrl+C to stop all services" 