# ADK Data Science Multi-Agent System Architecture

This document provides a comprehensive overview of the architecture for the ADK Data Science Multi-Agent Chatbot system, detailing the multi-agent design, data flow, and technical implementation.

## Table of Contents

- [System Overview](#system-overview)
- [Multi-Agent Architecture](#multi-agent-architecture)
- [Agent Communication](#agent-communication)
- [Data Flow](#data-flow)
- [Technology Stack](#technology-stack)
- [Security Considerations](#security-considerations)
- [Performance & Scalability](#performance--scalability)
- [Deployment Architecture](#deployment-architecture)
- [Monitoring & Observability](#monitoring--observability)

## System Overview

The ADK Data Science Multi-Agent Chatbot is a production-ready application that implements Google's Agent Development Kit (ADK) patterns for data science workflows. The system uses a multi-agent architecture where specialized agents handle different aspects of data science tasks, coordinated by a central orchestration agent.

### Key Design Principles

- **Modularity**: Each agent has a specific responsibility and can be developed/deployed independently
- **Scalability**: Agents can be scaled horizontally based on demand
- **Reliability**: Comprehensive error handling, health checks, and recovery mechanisms
- **Observability**: Extensive logging, monitoring, and performance tracking
- **Security**: Authentication, authorization, and secure communication between components

## Multi-Agent Architecture

### Agent Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                        Root Agent                            │
│                  (Orchestration Layer)                       │
│              Intent Classification & Routing                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
   ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
   │Database │   │Analytics│   │  BQML   │
   │ Agent   │   │ Agent   │   │ Agent   │
   └─────────┘   └─────────┘   └─────────┘
```

### 1. Root Agent (`app/data_science/agent.py`)

**Responsibilities:**
- Query intent classification using LLM-based analysis
- Agent routing and workflow orchestration
- Context management across multi-agent interactions
- Response aggregation and final output formatting

**Key Components:**
- `_classify_intent()`: Analyzes user queries to determine appropriate agent routing
- `_route_to_agents()`: Coordinates multi-agent workflows
- `_aggregate_responses()`: Combines outputs from multiple agents

**Intent Classification Categories:**
- **Database**: SQL queries, data retrieval, schema questions
- **Analytics**: Statistical analysis, EDA, visualizations
- **ML**: Machine learning, modeling, predictions
- **Complex**: Multi-agent workflows requiring coordination

### 2. Database Agent (`app/data_science/sub_agents/bigquery/`)

**Responsibilities:**
- SQL query generation and optimization
- BigQuery integration and data extraction
- Schema analysis and metadata retrieval
- Data validation and quality checks

**Key Features:**
- SQL syntax validation and optimization suggestions
- Automatic LIMIT clause addition for safety
- Table schema and statistics retrieval
- Query performance monitoring

**File Structure:**
```
bigquery/
├── __init__.py
├── agent.py          # Main database agent logic
└── tools.py          # BigQuery-specific tools and utilities
```

### 3. Analytics Agent (`app/data_science/sub_agents/analytics/`)

**Responsibilities:**
- Exploratory data analysis (EDA)
- Statistical analysis and hypothesis testing
- **Chart generation and execution**
- **Real-time visualization rendering**
- Correlation and trend analysis

**Capabilities:**
- Descriptive statistics calculation
- **Interactive chart generation (matplotlib, seaborn)**
- **Chart execution with PNG output**
- **Image serving via HTTP endpoints**
- Data profiling and quality assessment
- Statistical test recommendations

**Visualization Features:**
- **Automatic code generation for charts**
- **Backend chart execution using matplotlib**
- **Chart image storage and serving**
- **Frontend image rendering in chat interface**

**File Structure:**
```
analytics/
├── __init__.py
├── agent.py          # Main analytics agent logic with chart generation
└── tools.py          # Analytics tools and utilities

services/
├── chart_executor.py # Chart execution and image generation

api/
├── charts.py         # Chart image serving endpoints
```

### 4. BQML Agent (`app/data_science/sub_agents/bqml/`)

**Responsibilities:**
- Machine learning model development
- BigQuery ML integration
- Model training and evaluation
- Prediction and recommendation systems

**ML Capabilities:**
- Classification and regression models
- Time series forecasting
- Clustering and recommendation systems
- Model evaluation and performance metrics

**File Structure:**
```
bqml/
├── __init__.py
├── agent.py          # Main BQML agent logic
└── tools.py          # ML-specific tools and utilities
```

## Agent Communication

### ToolContext System

Agents communicate through a shared `ToolContext` object that maintains:

```python
class ToolContext:
    def __init__(self):
        self.state: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = []
    
    def update_state(self, key: str, value: Any)
    def get_state(self, key: str, default: Any = None)
    def add_to_history(self, agent: str, query: str, response: str)
```

**State Management:**
- `database_settings`: BigQuery configuration and schema information
- `query_result`: **Structured data from database queries (follows official ADK patterns)**
- `db_agent_output`: Formatted response text from database operations
- `analysis_artifacts`: Outputs from analytics operations
- `chart_data`: Generated chart information and image URLs
- `model_artifacts`: ML models and predictions

**History Tracking:**
- Complete interaction history across all agents
- Timestamped entries for audit and debugging
- Context preservation for follow-up queries

### Inter-Agent Communication Flow

```
User Query → Root Agent → Intent Classification
                ↓
    ┌─────────────────────────────────────┐
    │     Agent Routing Decision          │
    └─────────────────────────────────────┘
                ↓
    ┌─────────────────────────────────────┐
    │  Specialized Agent(s) Processing    │
    │  • Database query execution         │
    │  • Analytics computation            │
    │  • ML model operations             │
    └─────────────────────────────────────┘
                ↓
    ┌─────────────────────────────────────┐
    │     Context Update & Storage        │
    │  • Results stored in ToolContext    │
    │  • History updated                  │
    └─────────────────────────────────────┘
                ↓
    ┌─────────────────────────────────────┐
    │    Response Aggregation             │
    │  • Multi-agent output combination   │
    │  • Format for user presentation     │
    └─────────────────────────────────────┘
```

## Data Flow

### Request Processing Pipeline

1. **Frontend Request**: User submits query through React UI
2. **HTTP API**: FastAPI handles REST API communication
3. **FastAPI Router**: Routes request to appropriate endpoint
4. **Root Agent**: Receives and processes initial request
5. **Intent Classification**: **AI-powered classification (no hardcoded patterns)**
6. **Agent Execution**: **Sequential execution with data passing**
   - Database Agent: Retrieves and stores structured data
   - Analytics Agent: Processes data and generates visualizations
7. **Context Updates**: **Structured results stored following ADK patterns**
8. **Response Synthesis**: **Preserves charts and code, prevents text override**
9. **Chart Generation**: **Matplotlib execution and PNG image creation**
10. **Image Serving**: **HTTP endpoints serve chart images**
11. **Frontend Rendering**: **Markdown image parsing and display**

### Data Storage Strategy

**Temporary Storage:**
- In-memory session management for chat history
- Local file uploads for data processing
- Temporary artifacts during multi-agent workflows

**Persistent Storage (Future):**
- PostgreSQL for chat history and user sessions
- Google Cloud Storage for uploaded datasets
- BigQuery for processed data and analytics results

### File Processing Workflow

```
File Upload → Validation → Processing → Context Storage
     ↓             ↓           ↓           ↓
  Size/Type    Format Check  Parsing   Agent Access
  Validation   Content Scan  Analytics Available Data
```

## Technology Stack

### Backend Technologies

**Core Framework:**
- **FastAPI**: Async web framework for high performance
- **Python 3.9+**: Core programming language
- **Pydantic**: Data validation and serialization
- **Uvicorn**: ASGI server for production deployment

**AI/ML Integration:**
- **Google Generative AI**: Gemini-1.5-flash for LLM capabilities
- **Google Cloud BigQuery**: Data warehouse and analytics  
- **BigQuery ML**: Machine learning on large datasets
- **Matplotlib**: Chart generation and visualization
- **NumPy**: Scientific computing for data analysis

**Development Tools:**
- **Poetry**: Dependency management and packaging
- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Static type checking

**Testing Framework:**
- **pytest**: Testing framework
- **pytest-asyncio**: Async testing support
- **pytest-cov**: Coverage reporting
- **httpx**: HTTP client for testing

### Frontend Technologies

**Core Framework:**
- **React 18**: Modern React with concurrent features
- **TypeScript**: Type safety and developer experience
- **Vite**: Fast build tool and development server

**UI/UX:**
- **Tailwind CSS**: Utility-first CSS framework
- **Shadcn/ui**: High-quality React components
- **Lucide React**: Icon library

**State Management:**
- **Zustand**: Lightweight state management
- **React Query**: Server state management (future)

**Communication:**
- **HTTP REST API**: Synchronous request/response communication
- **Fetch API**: Modern HTTP client for API requests
- **Chart Image Loading**: Dynamic image rendering from backend URLs

## Security Considerations

### Authentication & Authorization

**Current Implementation:**
- No authentication (development/demo mode)
- CORS configuration for cross-origin requests
- Request validation using Pydantic models

**Production Security (Recommended):**
- JWT-based authentication
- Role-based access control (RBAC)
- API rate limiting
- Request/response encryption

### Data Security

**File Upload Security:**
- File type validation
- Size limits and scanning
- Temporary storage with cleanup
- Input sanitization

**API Security:**
- Request validation
- SQL injection prevention
- XSS protection
- Error message sanitization

### Google Cloud Security

**API Key Management:**
- Environment variable storage
- Key rotation policies
- Access logging and monitoring

**BigQuery Security:**
- Project-level permissions
- Dataset access controls
- Query audit logging

## Performance & Scalability

### Performance Optimizations

**Agent Performance:**
- Async/await for concurrent operations
- Connection pooling for database operations
- Response caching for repeated queries
- Lazy loading of expensive operations

**Frontend Performance:**
- Code splitting and lazy loading
- Optimized bundle sizes
- WebSocket connection management
- Efficient state updates

### Scalability Considerations

**Horizontal Scaling:**
- Stateless agent design
- External session storage
- Load balancer compatibility
- Database connection pooling

**Resource Management:**
- Memory-efficient data processing
- Streaming for large datasets
- Timeout management
- Resource cleanup

### Performance Monitoring

**Metrics Collection:**
- Response time tracking
- Error rate monitoring
- Resource utilization
- Agent performance benchmarks

**Benchmarking Framework:**
```python
# Example from eval/conftest.py
performance_benchmarks = {
    "response_time": {
        "excellent": 2.0,
        "good": 5.0,
        "acceptable": 10.0
    },
    "keyword_coverage": {
        "excellent": 0.8,
        "acceptable": 0.4
    }
}
```

## Deployment Architecture

### Development Environment

```
Frontend (Vite)     Backend (FastAPI)
Port: 5174     ←→   Port: 8000
                    ↓
               Google APIs
               • Gemini Pro
               • BigQuery
```

### Production Architecture (Recommended)

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │  Frontend CDN   │    │ Monitoring/Logs │
│   (nginx/ALB)   │    │    (CloudFront) │    │  (CloudWatch)   │
└─────────┬───────┘    └─────────────────┘    └─────────────────┘
          │
    ┌─────▼─────┐
    │  FastAPI  │
    │  Cluster  │
    │ (ECS/GKE) │
    └─────┬─────┘
          │
    ┌─────▼─────┐
    │  Database │
    │(PostgreSQL│
    │ /BigQuery)│
    └───────────┘
```

### Container Strategy

**Development:**
- Docker Compose for local development
- Hot reloading for rapid iteration
- Shared volumes for file uploads

**Production:**
- Multi-stage Docker builds
- Container orchestration (Kubernetes/ECS)
- Health checks and auto-scaling
- Blue-green deployments

## Monitoring & Observability

### Logging Strategy

**Structured Logging:**
```python
import logging
import structlog

logger = structlog.get_logger()

# Agent operation logging
logger.info(
    "agent_execution",
    agent_name="db_agent",
    query_type="sql_generation",
    execution_time=response_time,
    success=True
)
```

**Log Levels:**
- **ERROR**: Agent failures, API errors, system issues
- **WARNING**: Performance degradation, retry attempts
- **INFO**: Agent operations, user interactions
- **DEBUG**: Detailed execution flow (development only)

### Health Monitoring

**Agent Health Checks:**
```python
async def health_check_agent(agent):
    try:
        response = await agent.process_query("health check", context)
        return {"healthy": True, "response_time": time_taken}
    except Exception as e:
        return {"healthy": False, "error": str(e)}
```

**System Health Endpoints:**
- `/health`: Basic application health
- `/health/agents`: Individual agent status
- `/metrics`: Performance metrics (Prometheus format)

### Performance Metrics

**Key Performance Indicators:**
- Agent response times
- Query success rates
- Error frequency and types
- Resource utilization
- User session metrics

**Alerting Thresholds:**
- Response time > 10 seconds
- Error rate > 5%
- Agent health check failures
- Resource utilization > 80%

### Deployment Monitoring

**Deployment Tracking:**
```python
# deployment/deploy.py
deployment_results = {
    "deployment_id": f"deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    "agents": {
        "root_agent": {"status": "success", "health_check": {...}},
        "db_agent": {"status": "success", "health_check": {...}}
    },
    "status": "success"
}
```

**Rollback Capability:**
- Deployment state tracking
- Automated rollback on failure
- Health-based deployment validation

## Future Architecture Considerations

### Microservices Evolution

**Service Decomposition:**
- Independent agent services
- Dedicated databases per service
- Service mesh for communication
- API gateway for routing

### Event-Driven Architecture

**Event Streaming:**
- Apache Kafka for event streaming
- Event sourcing for audit trails
- CQRS for read/write separation
- Real-time analytics pipelines

### Machine Learning Operations (MLOps)

**Model Lifecycle Management:**
- Model versioning and registry
- Automated training pipelines
- A/B testing framework
- Model performance monitoring

This architecture provides a solid foundation for a production-ready multi-agent data science system while maintaining flexibility for future enhancements and scaling requirements.