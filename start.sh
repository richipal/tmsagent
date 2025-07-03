#!/bin/bash

# ADK Data Science Chatbot Startup Script
echo "🚀 Starting ADK Data Science Chatbot..."
echo "======================================"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "Checking prerequisites..."
if ! command_exists node; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ and try again."
    exit 1
fi

if ! command_exists python3; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+ and try again."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Setup backend
echo ""
echo "Setting up backend..."

echo "Setting up Python dependencies..."
if [ ! -d ".venv_full" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv_full
    source .venv_full/bin/activate
    pip install --upgrade pip
    pip install fastapi uvicorn google-generativeai numpy pandas matplotlib python-multipart aiofiles python-dotenv pyyaml google-cloud-bigquery google-auth google-auth-oauthlib authlib PyJWT
else
    echo "Virtual environment exists. Activating..."
    source .venv_full/bin/activate
    # Install auth dependencies if not already installed
    pip install google-auth google-auth-oauthlib authlib PyJWT
fi

# Setup ADK agent (optional)
if [ "$1" = "--setup-adk" ]; then
    echo "Setting up Google ADK integration..."
    python setup_adk.py
fi

# Copy environment file if it doesn't exist
if [ ! -f "backend/.env" ]; then
    echo "Creating .env file from template..."
    if [ -f "backend/.env.example" ]; then
        cp backend/.env.example backend/.env
    fi
fi

echo "✅ Backend setup completed"

# Setup frontend
echo ""
echo "Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

# Copy environment file if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo "Creating .env.local file from template..."
    cp .env.example .env.local
fi

echo "✅ Frontend setup completed"
cd ..

# Start services
echo ""
echo "Starting services..."
echo "🔧 Backend will start on http://localhost:8000"
echo "🌐 Frontend will start on http://localhost:5174"
echo ""

# Start backend in background
./backend/start_backend.sh &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Build frontend (only once if not built)
cd frontend
if [ ! -d "dist" ]; then
    echo "Building frontend..."
    npm run build
fi

# Start frontend using npm dev server
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Services started successfully!"
echo ""
echo "📱 Open your browser and navigate to: http://localhost:5174"
echo "📚 API documentation available at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Services stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for processes
wait
