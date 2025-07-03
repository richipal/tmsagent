#!/bin/bash

echo "🔧 Fixing authentication dependencies..."

# Navigate to project directory
cd /Users/richipalbindra/Documents/myhome/workspace/llm/google/adk/tmsagent

# Create a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install required packages
echo "📥 Installing packages..."
pip install fastapi uvicorn
pip install google-auth google-auth-oauthlib authlib PyJWT
pip install python-dotenv pydantic
pip install google-generativeai google-cloud-bigquery
pip install pandas numpy matplotlib plotly
pip install python-multipart aiofiles
pip install websockets

echo "✅ Dependencies installed successfully!"
echo "🚀 To run with authentication:"
echo "   source venv/bin/activate"
echo "   cd backend"
echo "   python main.py"