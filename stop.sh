#!/bin/bash

echo "🛑 Stopping ADK Data Science Chatbot services..."

# Stop backend (uvicorn main:app)
pkill -f "uvicorn main:app" 2>/dev/null && echo "✅ Backend stopped"
pkill -f "simple_main" 2>/dev/null && echo "✅ Legacy backend stopped"

# Stop frontend (npm dev server)
pkill -f "vite" 2>/dev/null && echo "✅ Frontend stopped"

# Stop any remaining processes on ports 8000 and 5174
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5174 | xargs kill -9 2>/dev/null

echo "🏁 All services stopped"