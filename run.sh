#!/bin/bash

# Quick run script for ADK Data Science Chatbot
echo "🚀 Starting ADK Data Science Chatbot (Quick Mode)..."
echo "======================================"

# Kill any existing processes
pkill -f "python main.py" 2>/dev/null
pkill -f "serve.py" 2>/dev/null
lsof -ti:5174 | xargs kill -9 2>/dev/null

# Start backend
echo "Starting backend on port 8000..."
cd backend
source venv/bin/activate
nohup python main.py > backend.log 2>&1 &

# Wait for backend to start
sleep 3

# Start frontend
echo "Starting frontend on port 5174..."
cd ../frontend
nohup python3 serve.py > server.log 2>&1 &

# Wait for frontend to start
sleep 2

echo ""
echo "✅ Services started successfully!"
echo ""
echo "📱 Frontend: http://localhost:5174"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "To stop services, run: ./stop.sh"