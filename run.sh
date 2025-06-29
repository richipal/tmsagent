#!/bin/bash

# Quick run script for ADK Data Science Chatbot
echo "🚀 Starting ADK Data Science Chatbot (Quick Mode)..."
echo "======================================"

# Kill any existing processes
pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "simple_main" 2>/dev/null
pkill -f "vite" 2>/dev/null
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5174 | xargs kill -9 2>/dev/null

# Start backend
echo "Starting full multi-agent backend on port 8000..."
nohup ./backend/start_backend.sh > backend.log 2>&1 &

# Wait for backend to start
sleep 3

# Start frontend
echo "Starting frontend on port 5174..."
cd frontend
nohup npm run dev > server.log 2>&1 &

# Wait for frontend to start
sleep 2

echo ""
echo "✅ Services started successfully!"
echo ""
echo "📱 Frontend: http://localhost:5174"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "To stop services, run: ./stop.sh"