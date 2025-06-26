#!/bin/bash

# Quick run script for ADK Data Science Chatbot
echo "🚀 Starting ADK Data Science Chatbot (Quick Mode)..."
echo "======================================"

# Kill any existing processes
pkill -f "chat-server" 2>/dev/null
pkill -f "vite" 2>/dev/null
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5174 | xargs kill -9 2>/dev/null

# Start backend
echo "Starting backend on port 8000..."
cd backend
nohup poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
cd ..

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