# ADK Data Science Chatbot - Current Working Version

A Time Management System (TMS) chatbot with a React frontend and simplified Python backend. This is the **currently working version** with basic functionality while dependency issues are resolved.

## 🚨 Current Status

**This system currently runs on a simplified backend due to dependency compatibility issues on Apple Silicon (M1/M2) Macs.**

### ✅ Working Features:
- Modern React frontend with TypeScript
- HTTP REST API communication
- Suggested questions with clickable interface
- Basic TMS query responses (keyword-based)
- Session management
- Clean, responsive UI with Tailwind CSS

### ⚠️ Temporary Limitations:
- Using simplified backend (`simple_main.py`) instead of full multi-agent system
- No BigQuery integration (requires dependency fixes)
- No chart generation (requires numpy/scipy fixes)
- Basic keyword-based responses instead of AI-powered analysis

## 🚀 Quick Start

### Prerequisites
- Node.js (v18+)
- Python (3.9+)

### 1. Start Backend
```bash
cd backend
python simple_main.py
```

### 2. Start Frontend (in new terminal)
```bash
cd frontend
npm install  # First time only
npm run dev
```

### 3. Access Application
- Frontend: http://localhost:5174
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 🛠️ Using Shell Scripts

```bash
# Start both services
./start.sh

# Quick background start
./run.sh

# Stop all services
./stop.sh
```

## 📁 Current Project Structure

```
├── backend/
│   ├── simple_main.py          # Current working backend
│   ├── main.py                 # Full backend (needs dependency fixes)
│   └── app/                    # Full multi-agent system (disabled)
├── frontend/                   # React TypeScript frontend
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── services/           # API services
│   │   ├── stores/             # Zustand state management
│   │   └── types/              # TypeScript definitions
│   └── package.json
├── pyproject.toml              # Poetry configuration
├── start.sh, stop.sh, run.sh   # Shell scripts
└── documentation files
```

## 🔧 Available Queries

The simplified backend responds to these sample queries:

- "List all users"
- "List all the 21st century activity codes"
- "Show me the top 5 employees by hours worked"
- "Show me absence patterns by day of week"
- "Hello" / "Hi"

## 🧪 Testing the API

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test chat endpoint
curl -X POST http://localhost:8000/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{"message": "List all the 21st century activity codes", "session_id": "test"}'

# Test suggested questions
curl http://localhost:8000/api/suggested-questions
```

## 🔄 Restoring Full Functionality

To restore the complete ADK multi-agent system:

### 1. Fix Dependency Issues
```bash
# Remove incompatible packages
poetry remove numpy pandas matplotlib scikit-learn seaborn

# Install ARM64 compatible versions
poetry add numpy pandas matplotlib --platform=darwin_arm64

# OR use conda for better ARM64 support
conda create -n adk python=3.9
conda activate adk
conda install numpy pandas matplotlib scipy scikit-learn
```

### 2. Fix Google AI API Version
```bash
# Install compatible version
poetry add google-generativeai==0.8.3
```

### 3. Switch to Full Backend
```bash
# Update shell scripts to use main.py
cd backend
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Test Full System
```bash
# Run tests
poetry run pytest

# Test BigQuery integration
# (requires GOOGLE_API_KEY and GOOGLE_CLOUD_PROJECT in .env)
```

## 📚 Architecture Overview

### Current Architecture (Simplified)
```
Frontend (React) ←→ Simple Backend (FastAPI) 
     ↓                      ↓
HTTP API              Keyword Responses
```

### Target Architecture (When Fixed)
```
Frontend ←→ FastAPI ←→ Multi-Agent System
                           ├── Root Agent
                           ├── Database Agent (BigQuery)
                           ├── Analytics Agent (Charts)
                           └── ML Agent (BQML)
```

## 🆘 Troubleshooting

### "Failed to fetch" Error
- Ensure backend is running: `curl http://localhost:8000/health`
- Check console for CORS errors
- Verify frontend is connecting to correct URL

### Backend Won't Start
- Check for port conflicts: `lsof -i :8000`
- Try simple backend: `python simple_main.py`
- Check Python dependencies

### Frontend Issues
- Clear npm cache: `npm cache clean --force`
- Reinstall dependencies: `rm -rf node_modules && npm install`
- Check browser console for JavaScript errors

## 📄 Documentation

- `CLAUDE.md` - Development guidance and patterns
- `ARCHITECTURE.md` - Full system architecture (target state)
- `SUGGESTED_QUESTIONS.md` - Sample queries for the system

## 🤝 Contributing

When the full system is restored:
1. Run tests: `poetry run pytest`
2. Check code quality: `poetry run black backend/ && poetry run mypy backend/app/`
3. Test both frontends work with your changes

---

**Note**: This README reflects the current working state. See the full `README.md` for the complete system documentation once dependency issues are resolved.