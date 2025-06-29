# Claude Code Development Patterns and Fixes

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository, including critical patterns, fixes, and lessons learned during implementation.

## Current System Status

**⚠️ IMPORTANT: The system currently runs on a simplified backend due to dependency issues.**

### Working Components:
- ✅ Frontend (React + TypeScript) - Fully functional
- ✅ Simple Backend (`simple_main.py`) - Working with basic responses
- ✅ Suggested Questions API - Functional
- ✅ HTTP REST API - Working
- ✅ Shell scripts (start.sh, stop.sh, run.sh) - Updated to use simple backend

### Issues with Full Backend:
- ❌ numpy/scipy architecture incompatibility on Apple Silicon (M1/M2 Macs)
- ❌ Google GenerativeAI version compatibility issues
- ❌ Chart generation requires scipy dependencies
- ❌ Full multi-agent system requires dependency resolution

### To Restore Full Functionality:
1. Fix numpy architecture issues (install ARM64 compatible packages)
2. Resolve Google GenerativeAI API compatibility
3. Switch back to `main.py` backend
4. Test BigQuery integration

## Common Development Commands

### Backend Development
```bash
# Start development server (current working version)
cd backend && python simple_main.py             # Runs on port 8000

# Start full backend (requires dependency fixes)
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Run tests
poetry run pytest                                # All tests
poetry run pytest tests/ -v                      # Unit tests only
poetry run pytest eval/ -v -m evaluation         # Agent evaluation tests
poetry run pytest --cov=app --cov-report=html    # With coverage report

# Code quality checks - run these before committing
poetry run black backend/                        # Format code
poetry run isort backend/                        # Sort imports
poetry run mypy backend/app/                     # Type checking
```

### Frontend Development
```bash
# Start development server
npm run dev                                      # Runs on port 5174

# Build for production
npm run build                                    # Creates dist/ directory
npm run preview                                  # Preview production build
```

### Full Stack Development
```bash
# Using shell scripts (uses simple backend)
./start.sh                                       # Start all services
./stop.sh                                        # Stop all services
./run.sh                                         # Quick start with background processes

# Manual startup
cd backend && python simple_main.py &           # Start backend in background
cd frontend && npm run dev                       # Start frontend

# Using Docker Compose (may require dependency fixes)
docker-compose up --build                        # Start all services
```

## High-Level Architecture

This is a **Multi-Agent Data Science System** implementing Google's official ADK patterns with the following architecture:

### Agent System Design
The system replicates the official Google ADK structure with specialized agents:

1. **Root Agent** (`backend/app/data_science/agent.py`): 
   - Entry point for all queries
   - Performs intent classification using Gemini Pro
   - Routes queries to appropriate specialized agents
   - Maintains conversation context via ToolContext

2. **Specialized Sub-Agents** (`backend/app/data_science/sub_agents/`):
   - **BigQuery Agent** (`bigquery/agent.py`): NL2SQL conversion and query execution
     - Uses `initial_bq_nl2sql` tool for natural language to SQL conversion
     - Uses `run_bigquery_validation` tool for query validation and execution
     - Follows official ADK patterns with proper error handling and response formatting
   - **Analytics Agent** (`analytics/agent.py`): Statistical analysis and data science operations
     - Provides comprehensive data analysis with Python code examples
     - Generates insights and recommendations
     - Context-aware analysis based on available data
   - **BQML Agent** (`bqml/agent.py`): Machine learning recommendations using BigQuery ML
     - ML model selection and feature engineering guidance
     - BQML-specific SQL generation for model training and prediction
     - Deployment and monitoring recommendations

### Inter-Agent Communication
- Agents communicate through a shared `ToolContext` object
- Context preserves state across agent interactions
- Results from one agent can be used by another
- Session management maintains conversation history

### Frontend-Backend Communication
- **REST API**: HTTP communication for reliable chat messaging
- **Chart Serving**: Image serving via `/api/charts/{filename}` endpoints
- **File Uploads**: Multipart form data to `/api/upload` endpoint
- Frontend uses Zustand for state management with auto-focus input

### Key Design Patterns
1. **Tool-Based Architecture**: Each agent has specific tools (functions) it can execute
2. **Async Processing**: All agent operations are async for concurrent execution
3. **Session Isolation**: Each chat session has isolated context and state
4. **File Processing Pipeline**: Upload → Validation → Storage → Agent Access

## Critical Implementation Patterns

### 1. Agent Routing (Root Agent)
**CRITICAL**: Never use hardcoded patterns. Always use AI-powered intent classification.

```python
# app/data_science/agent.py - Correct routing approach
if "call_db_agent" in primary_agent_normalized:
    db_response = await self._route_to_database_agent(query, context)
    responses.append(db_response)
```

### 2. Response Synthesis
**CRITICAL**: Preserve charts and code responses, never override with text.

```python
# Check if any response contains Python code or chart URLs - preserve it
chart_or_code_response = None
for response in responses:
    if "```python" in response or "/api/charts/" in response or "![Bar Chart]" in response:
        chart_or_code_response = response
        break
```

### 3. Database Agent Tool Implementation
**CRITICAL**: Follow official ADK tool patterns exactly.

```python
# Store structured data for other agents (official ADK pattern)
if callback_context:
    callback_context.update_state("query_result", validation_result)
```

## Common Errors and Fixes

### 1. "Sorry, I encountered an error"
**Problem**: Backend server not running or dependencies missing
**Solution**: 
```bash
cd backend
poetry install  # Install all dependencies including matplotlib
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. SQL Aggregation Errors
**Problem**: "column is neither grouped nor aggregated"
**Fix**: Ensure proper GROUP BY in generated SQL
```sql
-- Correct for comparisons
SELECT category, SUM(total_amount) AS total_sales 
FROM sales_data 
GROUP BY category
```

### 3. Python Code Instead of Answers
**Problem**: Queries returning code blocks instead of executing
**Root Cause**: Routing logic using string matching instead of tool names
**Fix**: Update routing to check tool names: `"call_db_agent" in primary_agent_normalized`

### 4. Charts Not Displaying
**Problem**: "See attached bar chart" text without actual chart
**Solution**: Implement complete chart pipeline:
1. Chart Executor Service (`backend/app/services/chart_executor.py`)
2. Image Serving API (`backend/app/api/charts.py`)
3. Frontend Markdown Parsing (`frontend/src/components/chat/message-bubble.tsx`)

### 5. ModuleNotFoundError: matplotlib
**Fix**: Add to requirements.txt:
```txt
matplotlib>=3.7.0
seaborn>=0.12.0
```

## Chart Generation Implementation

### Complete Pipeline

**Analytics Agent Integration**:
```python
from app.services.chart_executor import chart_executor

if "chart" in query.lower() or "bar" in query.lower():
    chart_result = chart_executor.execute_chart_code(chart_code)
    if chart_result["success"]:
        return f"Analysis complete. ![Bar Chart]({chart_result['url']})"
```

**Frontend Auto-Focus**:
```typescript
// chat-input.tsx
useEffect(() => {
    if (textareaRef.current) {
        textareaRef.current.focus();
    }
}, []);
```

**Image Rendering**:
```typescript
// message-bubble.tsx
const absoluteSrc = src.startsWith('/') ? `http://localhost:8000${src}` : src;
```

## Development Guidelines

### Adding New Agent Capabilities
1. Add new tools to existing agents in `backend/app/data_science/sub_agents/`
2. Update the agent's tool registry
3. Add corresponding tests in `tests/` and `eval/`
4. Update intent classification in root agent if needed

### Modifying Frontend Components
1. Components use Shadcn/ui - check existing patterns in `frontend/src/components/ui/`
2. API calls go through `frontend/src/services/api.ts`
3. HTTP API calls go through fetch requests to backend
4. State management uses Zustand stores in `frontend/src/stores/`

### Testing Requirements
- Add unit tests for new functions
- Add integration tests for new API endpoints
- Add evaluation tests for new agent capabilities
- Maintain test coverage above existing levels

### Code Style
- Backend: Black formatting, 100 char line length, type hints required
- Frontend: TypeScript strict mode, follow existing component patterns
- Both: Clear function/variable names, avoid abbreviations

## Important Context

### BigQuery Integration
- Agents can execute BigQuery queries via the Database Agent
- BQML Agent handles ML model creation and predictions
- Ensure proper dataset/table references in queries

### File Processing
- Supported formats: CSV, JSON, Excel, Parquet
- Files stored in `backend/uploads/` directory
- 50MB default size limit
- Files are parsed and made available to agents via context

### Session Management
- Sessions are currently in-memory (will be lost on server restart)
- Each session maintains its own agent context and chat history
- WebSocket connections are session-specific

### Deployment
- Deployment scripts in `deployment/` directory
- Configuration in `deployment/config.yaml`
- Health checks and monitoring built-in
- Rollback capabilities included

## ADK Compliance

This implementation **fully replicates** the official Google ADK patterns with key enhancements:

### Official ADK Structure
- **Agent Classes**: Follows official ADK agent patterns with proper initialization
- **Tool Integration**: Uses official `initial_bq_nl2sql` and `run_bigquery_validation` tools
- **Environment Configuration**: Supports ADK environment variables
- **Response Formatting**: Matches official ADK response patterns

### Key Features Implemented
- **NL2SQL Conversion**: Proper prompt engineering and SQL cleaning
- **Chart Generation**: Complete matplotlib pipeline with PNG serving
- **Agent Coordination**: Proper callback context and state management
- **Auto-focus Input**: Enhanced UX with automatic input focus
- **Image Rendering**: Markdown parsing for chart display in frontend

### Critical Implementation Notes
1. **Never hardcode routing logic** - always use AI classification
2. **Follow official ADK structure exactly** - implement tools properly
3. **Chart pipeline must be complete** - generation, execution, serving, rendering
4. **Use HTTP REST API** - not WebSocket for this implementation
5. **Preserve chart responses** - never override with text in synthesis

### Test Queries That Should Work
- "What's the average transaction amount?" → Direct numerical answer
- "Which sales rep has the highest revenue?" → Name and amount
- "Compare sales between product categories" → Category totals
- "How many premium vs standard customers do we have?" → Counts
- "How many premium vs standard customers do we have show in barchart?" → Chart display

### Environment Variables
- `BIGQUERY_AGENT_MODEL`: Model for BigQuery agent (default: gemini-1.5-flash)
- `ANALYTICS_AGENT_MODEL`: Model for Analytics agent (default: gemini-1.5-flash)
- `BQML_AGENT_MODEL`: Model for BQML agent (default: gemini-1.5-flash)
- `NL2SQL_METHOD`: NL2SQL conversion method (default: BASELINE)

### URLs and Access
- Backend: http://localhost:8000
- Frontend: http://localhost:5174
- API Docs: http://localhost:8000/docs
- Charts: http://localhost:8000/api/charts/{filename}

This implementation now functions identically to the official Google ADK samples with enhanced chart visualization capabilities.