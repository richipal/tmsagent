#!/bin/bash

echo "🛑 Stopping ADK Data Science Chatbot services..."

# Stop Python processes (backend)
pkill -f "python main.py" 2>/dev/null && echo "✅ Backend stopped"

# Stop Python server (frontend)
pkill -f "serve.py" 2>/dev/null && echo "✅ Frontend stopped"

# Stop any remaining Python servers on port 5174
lsof -ti:5174 | xargs kill -9 2>/dev/null

echo "🏁 All services stopped"