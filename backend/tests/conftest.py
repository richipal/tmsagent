"""
Pytest configuration and shared fixtures
"""

import pytest
import os
import tempfile
import shutil
from typing import Generator
from datetime import datetime
from unittest.mock import Mock, patch

# Set test environment variables FIRST
def setup_test_environment():
    """Set up test environment variables"""
    test_env = {
        "TESTING": "true",
        "GOOGLE_API_KEY": "test-api-key",
        "GOOGLE_CLOUD_PROJECT": "test-project",
        "BIGQUERY_DATASET_ID": "test_dataset",
        "DATABASE_PATH": ":memory:",
    }
    for key, value in test_env.items():
        os.environ[key] = value

# Initialize test environment BEFORE imports
setup_test_environment()

# Now safe to import
try:
    from app.database.models import DatabaseManager
except ImportError as e:
    DatabaseManager = None
    print(f"Warning: Could not import DatabaseManager: {e}")

try:
    from app.core.persistent_session_manager import PersistentSessionManager
except ImportError as e:
    PersistentSessionManager = None
    print(f"Warning: Could not import PersistentSessionManager: {e}")

try:
    from app.data_science.tools import ToolContext
except ImportError as e:
    ToolContext = None
    print(f"Warning: Could not import ToolContext: {e}")


@pytest.fixture
def temp_db_path():
    """Create a temporary database path for testing"""
    # Use in-memory database for tests to avoid locking issues
    yield ":memory:"


@pytest.fixture
def test_db_manager(temp_db_path):
    """Create a test database manager with temporary database"""
    if DatabaseManager is None:
        pytest.skip("DatabaseManager not available")
    
    db_manager = DatabaseManager(db_path=temp_db_path)
    yield db_manager
    
    # Close database connection
    try:
        db_manager.close()
    except:
        pass


@pytest.fixture
def test_session_manager(test_db_manager, monkeypatch):
    """Create a test session manager with temporary database"""
    if PersistentSessionManager is None:
        pytest.skip("PersistentSessionManager not available")
    
    try:
        # Monkey patch the global db_manager in the persistent_session_manager module
        import app.core.persistent_session_manager
        monkeypatch.setattr(app.core.persistent_session_manager, 'db_manager', test_db_manager)
        
        session_manager = PersistentSessionManager()
        yield session_manager
    except ImportError:
        pytest.skip("PersistentSessionManager module not available")


@pytest.fixture
def sample_session_data():
    """Sample session data for testing"""
    return {
        "session_id": "test-session-123",
        "title": "Test Session",
        "messages": [
            {
                "content": "Where does Rosalinda Rodriguez work?",
                "role": "user"
            },
            {
                "content": "075: BUSINESS TECHNOLOGY DEPARTMENT",
                "role": "assistant"
            }
        ]
    }


@pytest.fixture
def sample_context():
    """Sample tool context for testing"""
    if ToolContext is None:
        pytest.skip("ToolContext not available")
    
    context = ToolContext()
    context.update_state("session_id", "test-session-123")
    context.update_state("last_query", "Where does Rosalinda Rodriguez work?")
    context.update_state("last_response", "075: BUSINESS TECHNOLOGY DEPARTMENT")
    context.update_state("query_result", {
        "success": True,
        "data": [{"code": "075", "name": "BUSINESS TECHNOLOGY DEPARTMENT"}],
        "row_count": 1
    })
    return context


@pytest.fixture
def mock_agent_response():
    """Mock agent response for testing"""
    def _mock_response(query: str, context: any):
        if "rosalinda" in query.lower():
            return "075: BUSINESS TECHNOLOGY DEPARTMENT"
        elif "who else works here" in query.lower():
            return "John Doe, Jane Smith, Bob Johnson"
        else:
            return "I don't know the answer to that question."
    return _mock_response


@pytest.fixture
def mock_gemini_model():
    """Mock Gemini model for testing"""
    mock_model = Mock()
    mock_response = Mock()
    mock_response.candidates = [Mock()]
    mock_response.candidates[0].content.parts = [Mock()]
    mock_response.candidates[0].content.parts[0].text = "SELECT * FROM employees LIMIT 10"
    mock_model.generate_content.return_value = mock_response
    return mock_model


@pytest.fixture
def client():
    """Create test client for API testing"""
    try:
        from fastapi.testclient import TestClient
        from main import app
        
        with TestClient(app) as test_client:
            yield test_client
    except ImportError as e:
        pytest.skip(f"FastAPI TestClient or main app not available: {e}")


@pytest.fixture(autouse=True)
def reset_singleton_instances():
    """Reset singleton instances between tests"""
    yield
    # Cleanup any singleton state if needed