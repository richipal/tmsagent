# ADK Data Science Multi-Agent Chatbot

A production-ready chatbot application built with Google's ADK (Agent Development Kit) data science multi-agent system. Features a modern React frontend and FastAPI backend with comprehensive testing, deployment, and evaluation capabilities following Google ADK best practices.

## 🤖 Multi-Agent Architecture

This application implements a sophisticated multi-agent system for data science tasks:

- **Root Agent**: Orchestrates and routes queries to specialized sub-agents
- **Database Agent**: Handles SQL queries, data extraction, and BigQuery operations  
- **Analytics Agent**: Performs statistical analysis, visualizations, and exploratory data analysis
- **BQML Agent**: Manages machine learning tasks using BigQuery ML

## 🚀 Features

### Frontend
- **Modern React 18+ with TypeScript** for type safety and performance
- **Tailwind CSS + Shadcn/ui** for polished, responsive design
- **HTTP REST API communication** for reliable chat experiences
- **Dark/Light theme toggle** with system preference detection
- **File upload with drag-and-drop** for seamless data analysis
- **Syntax highlighting** for code responses and queries
- **Export functionality** for chat history (JSON, CSV, TXT formats)
- **Advanced message search** and comprehensive session management

### Backend
- **FastAPI** with async/await for high-performance API operations
- **Multi-agent orchestration** with intelligent query routing
- **Google Generative AI integration** (Gemini-1.5-flash) for natural language processing
- **BigQuery integration** for large-scale data operations
- **Chart generation and visualization** with matplotlib and PNG serving
- **Comprehensive file processing** for datasets (CSV, JSON, Excel, Parquet)
- **Advanced session management** with context preservation
- **Production-ready CORS and security configurations**

### Testing & Quality Assurance
- **Comprehensive test suite** with unit, integration, and evaluation tests
- **Agent capability evaluations** with performance benchmarks
- **Code quality tools** (Black, isort, flake8, mypy)
- **Automated CI/CD pipeline** with GitHub Actions
- **Coverage reporting** and security scanning

### Deployment & Operations
- **Production deployment scripts** with health monitoring
- **Configuration management** with YAML-based settings
- **Docker containerization** for consistent environments
- **Poetry dependency management** for reliable builds
- **Automated deployment** with status monitoring

## 📋 Prerequisites

- **Node.js** (v18 or higher)
- **Python** (3.9 or higher) 
- **Poetry** (for dependency management)
- **Google API Key** for Gemini-1.5-flash access
- **Git**
- **Google Cloud Project** with BigQuery and Generative AI APIs enabled
- **Google API Key** for Gemini Pro access

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd chatbot-project
```

### 2. Backend Setup (Using Poetry)

```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Copy environment file
cp backend/.env.example backend/.env

# Edit .env file with your Google Cloud configuration
# Required: GOOGLE_API_KEY, GOOGLE_CLOUD_PROJECT
# Note: matplotlib and seaborn for chart generation are included
nano backend/.env
```

### 3. Alternative Backend Setup (Using pip)

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows

# Install dependencies
pip install -r requirements.txt
# This includes matplotlib, seaborn for chart generation

# Copy and configure environment file
cp .env.example .env
nano .env
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file (optional)
cp .env.example .env.local
```

### 5. Environment Configuration

Configure your backend `.env` file with required Google Cloud settings:

```env
# Google Cloud Configuration
GOOGLE_API_KEY=your_gemini_api_key_here
GOOGLE_CLOUD_PROJECT=your_gcp_project_id

# Application Settings
DEBUG=true
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
ALLOWED_ORIGINS=http://localhost:5174

# File Processing
MAX_FILE_SIZE=52428800
UPLOAD_DIR=uploads
```

## 🏃‍♂️ Running the Application

### Method 1: Using Poetry (Recommended)

```bash
# Start backend server
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# In a new terminal, start frontend
cd frontend
npm run dev
```

### Method 2: Using Virtual Environment

```bash
# Start backend server
cd backend
source venv/bin/activate  # Activate virtual environment
python main.py

# In a new terminal, start frontend
cd frontend
npm run dev
```

### Method 3: Using Poetry Scripts

```bash
# Start backend using poetry script
poetry run chat-server

# In a new terminal, start frontend
cd frontend
npm run dev
```

**Access URLs:**
- Backend API: `http://localhost:8000`
- Frontend UI: `http://localhost:5174` 
- API Documentation: `http://localhost:8000/docs`
- Chart Images: `http://localhost:8000/api/charts/{chart_filename}`

## 🐳 Docker Setup

### Using Docker Compose (Recommended)

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d --build
```

### Individual Docker Commands

#### Backend
```bash
cd backend
docker build -t chatbot-backend .
docker run -p 8000:8000 chatbot-backend
```

#### Frontend
```bash
cd frontend
docker build -t chatbot-frontend .
docker run -p 3000:3000 chatbot-frontend
```

## 🧪 Testing & Quality Assurance

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run unit tests only
poetry run pytest tests/ -v

# Run integration tests
poetry run pytest tests/ -v -m integration

# Run evaluation tests for agent capabilities
poetry run pytest eval/ -v -m evaluation

# Run tests with coverage
poetry run pytest --cov=app --cov-report=html
```

### Code Quality

```bash
# Format code
poetry run black backend/
poetry run isort backend/

# Lint code
poetry run flake8 backend/

# Type checking
poetry run mypy backend/app/
```

### Agent Deployment Testing

```bash
# Test deployment scripts
poetry run pytest deployment/test_deployment.py -v

# Test agent deployment status
poetry run python deployment/deploy.py --action status

# Deploy agents (for testing)
poetry run python deployment/deploy.py --action deploy
```

## 📁 Project Structure

```
chatbot-project/
├── frontend/                    # React TypeScript frontend
│   ├── src/
│   │   ├── components/         # React components
│   │   │   ├── chat/           # Chat interface components
│   │   │   ├── sidebar/        # Navigation and session management
│   │   │   └── ui/             # Shadcn/ui components
│   │   ├── hooks/              # Custom React hooks
│   │   ├── services/           # API and WebSocket services
│   │   ├── stores/             # Zustand state management
│   │   ├── types/              # TypeScript type definitions
│   │   └── styles/             # Global styles
│   ├── package.json
│   └── tailwind.config.js
├── backend/                     # FastAPI Python backend
│   ├── app/
│   │   ├── api/                # API route handlers
│   │   │   ├── chat.py         # Chat endpoints
│   │   │   ├── upload.py       # File upload endpoints
│   │   │   └── charts.py       # Chart image serving endpoints
│   │   ├── data_science/       # Multi-agent system
│   │   │   ├── agent.py        # Root orchestration agent
│   │   │   ├── sub_agents/     # Specialized agents
│   │   │   │   ├── bigquery/   # Database agent
│   │   │   │   ├── analytics/  # Analytics agent with chart generation
│   │   │   │   └── bqml/       # ML agent
│   │   │   └── tools.py        # Agent tools and utilities
│   │   ├── services/           # Core services
│   │   │   └── chart_executor.py # Chart execution and image generation
│   │   ├── core/               # Core business logic
│   │   └── models/             # Pydantic models
│   ├── requirements.txt
│   └── main.py
├── tests/                       # Unit and integration tests
│   ├── test_root_agent.py      # Root agent tests
│   ├── test_sub_agents.py      # Sub-agent tests
│   ├── test_api_integration.py # API integration tests
│   └── test_tools.py           # Tool and utility tests
├── eval/                        # Agent capability evaluations
│   ├── test_agent_capabilities.py # Performance evaluations
│   └── conftest.py             # Evaluation fixtures
├── deployment/                  # Deployment and operations
│   ├── deploy.py               # Deployment scripts
│   ├── test_deployment.py      # Deployment tests
│   └── config.yaml             # Deployment configuration
├── .github/workflows/           # CI/CD pipeline
├── pyproject.toml              # Poetry configuration
└── ARCHITECTURE.md             # Detailed architecture documentation
```

## 🔧 Configuration

### Backend Configuration (.env)

```env
DEBUG=true
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
ALLOWED_ORIGINS=http://localhost:3000
MAX_FILE_SIZE=52428800
UPLOAD_DIR=uploads
```

### Frontend Configuration (.env.local)

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## 🤖 Multi-Agent System Details

The application implements a sophisticated multi-agent architecture based on Google ADK patterns:

### Agent Capabilities

1. **Root Agent** (`backend/app/data_science/agent.py`):
   - Intent classification and query routing
   - Multi-agent orchestration and workflow management
   - Context preservation across agent interactions

2. **Database Agent** (`backend/app/data_science/sub_agents/bigquery/`):
   - SQL query generation and optimization
   - BigQuery integration and data extraction
   - Schema analysis and table information retrieval

3. **Analytics Agent** (`backend/app/data_science/sub_agents/analytics/`):
   - Statistical analysis and data exploration
   - **Chart generation and execution** with matplotlib and seaborn
   - **Real-time chart image serving** via HTTP endpoints
   - **Frontend chart display** with markdown image parsing
   - Correlation analysis and trend identification

4. **BQML Agent** (`backend/app/data_science/sub_agents/bqml/`):
   - Machine learning model creation and training
   - BigQuery ML integration
   - Prediction and recommendation systems

### Agent Communication

Agents communicate through a shared `ToolContext` that maintains:
- Query history and responses
- Shared state and artifacts
- Data processing results
- Model outputs and predictions

For detailed architecture information, see [ARCHITECTURE.md](ARCHITECTURE.md).

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

- `POST /api/chat/send` - Send message to AI agent
- `GET /api/chat/history/{session_id}` - Get chat history
- `POST /api/upload` - Upload files for analysis
- `GET /api/export/{session_id}` - Export chat history
- `GET /api/charts/{chart_filename}` - Serve chart images

## 🎨 UI Components

The frontend uses Shadcn/ui components for a consistent, polished interface:

- **Chat Interface**: Message bubbles, typing indicators, timestamps
- **Sidebar**: Session management, theme toggle, search functionality
- **File Upload**: Drag-and-drop interface with progress indicators
- **Code Highlighting**: Syntax highlighting for AI code responses
- **Responsive Design**: Mobile-friendly layout

## 🔍 Features in Detail

### Real-time Chat
- HTTP REST API for reliable messaging
- Typing indicators and message status
- Auto-scroll to latest messages
- **Chart visualization** with inline image rendering

### File Upload & Processing
- Support for CSV, JSON, Excel, TXT files
- Drag-and-drop interface
- File validation and size limits
- Integration with ADK for data analysis

### Theme System
- Light/Dark mode toggle
- System preference detection
- Consistent theming across components

### Export Functionality
- Export chat history in multiple formats
- JSON, CSV, and TXT formats supported
- Downloadable files with proper naming

### Chart Generation and Visualization

The system supports a complete chart generation and visualization pipeline following Google ADK patterns:

**Chart Generation Workflow:**
1. User requests visualization (e.g., "show in barchart")
2. Analytics Agent generates matplotlib/seaborn code
3. Chart Executor service executes code and saves PNG image
4. Chart URL returned in markdown format: `![Chart](/api/charts/filename.png)`
5. Frontend parses markdown and displays chart inline

**Example Queries:**
- "How many premium vs standard customers do we have show in barchart?"
- "Compare sales between product categories with chart"
- "Show revenue trends over time as line chart"

**Technical Implementation:**
- **Chart Executor**: `backend/app/services/chart_executor.py`
- **Image Serving**: `backend/app/api/charts.py` 
- **Frontend Rendering**: `frontend/src/components/chat/message-bubble.tsx`
- **Auto-focus Input**: Text input automatically focused for better UX

**Supported Visualizations:**
- Bar charts, line plots, histograms, scatter plots
- Correlation matrices, statistical distributions
- Custom matplotlib/seaborn charts with PNG output

## 🚀 Production Deployment

### Using Poetry (Recommended)

```bash
# Build frontend
cd frontend
npm run build

# Install production dependencies
poetry install --without dev

# Deploy agents
poetry run python deployment/deploy.py --action deploy

# Start production server
poetry run uvicorn main:app --host 0.0.0.0 --port 8000
```

### Using Docker

```bash
# Build and deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up --build

# Or deploy agents manually
poetry run deploy --action deploy --config deployment/config.yaml
```

### Environment Variables for Production

```env
# Production settings
DEBUG=false
LOG_LEVEL=WARNING
ALLOWED_ORIGINS=https://yourdomain.com

# Google Cloud Production
GOOGLE_CLOUD_PROJECT=your-production-project
GOOGLE_API_KEY=your-production-api-key

# Security
CORS_ALLOW_CREDENTIALS=false
MAX_CONCURRENT_REQUESTS=100
```

### Health Monitoring

```bash
# Check agent deployment status
poetry run python deployment/deploy.py --action status

# Monitor agent health
curl http://localhost:8000/health

# View deployment logs
tail -f deployment/state/*.json
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Check the [API documentation](http://localhost:8000/docs)
- Review the [project structure](#project-structure)
- Open an issue on GitHub

## 🔮 Future Enhancements

### Core Features
- [ ] Persistent database storage (PostgreSQL/MongoDB)
- [ ] User authentication and authorization 
- [ ] Advanced data visualization capabilities
- [ ] Real-time collaboration features
- [ ] Mobile application (React Native)

### Agent Enhancements
- [ ] Additional specialized agents (NLP, Computer Vision)
- [ ] Agent performance optimization and caching
- [ ] Custom agent development framework
- [ ] Agent marketplace and plugin system

### Enterprise Features
- [ ] Multi-tenant support
- [ ] Advanced security and compliance
- [ ] Enterprise SSO integration
- [ ] Advanced monitoring and analytics
- [ ] Horizontal scaling with Kubernetes

### Developer Experience
- [ ] Agent debugging and profiling tools
- [ ] Visual agent workflow builder
- [ ] Advanced testing and simulation framework
- [ ] Performance benchmarking suite

## 📊 Performance & Monitoring

The system includes comprehensive monitoring:

- **Agent Performance Metrics**: Response times, success rates, error tracking
- **Health Checks**: Automated agent health monitoring with alerts  
- **Load Testing**: Evaluation tests for performance under load
- **Deployment Tracking**: Complete deployment state and rollback capabilities

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed performance considerations and monitoring setup.