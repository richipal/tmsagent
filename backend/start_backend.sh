#!/bin/bash

# Backend startup script with proper virtual environment
cd "$(dirname "$0")"
PROJECT_ROOT="$(cd .. && pwd)"

echo "Starting backend from: $(pwd)"
echo "Project root: $PROJECT_ROOT"

# Activate virtual environment
source "$PROJECT_ROOT/.venv_full/bin/activate"

# Set Python path
export PYTHONPATH="$(pwd)"

# Start uvicorn server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload