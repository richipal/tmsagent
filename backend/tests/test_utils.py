"""
Test utilities and helper functions
"""

import os
import tempfile
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, AsyncMock
from app.models.chat import MessageRole, ChatSession, Message
from app.data_science.tools import ToolContext


class MockGeminiModel:
    """Mock Gemini model for consistent testing"""
    
    def __init__(self, default_response: str = "Default test response"):
        self.default_response = default_response
        self.call_history = []
        self.response_queue = []
    
    def generate_content(self, prompt: str) -> Mock:
        """Generate mock content response"""
        self.call_history.append(prompt)
        
        # Use queued response if available, otherwise default
        response_text = self.response_queue.pop(0) if self.response_queue else self.default_response
        
        mock_response = Mock()
        mock_response.candidates = [Mock()]
        mock_response.candidates[0].content.parts = [Mock()]
        mock_response.candidates[0].content.parts[0].text = response_text
        
        return mock_response
    
    def queue_response(self, response: str):
        """Queue a specific response for the next call"""
        self.response_queue.append(response)
    
    def queue_responses(self, responses: List[str]):
        """Queue multiple responses"""
        self.response_queue.extend(responses)
    
    def get_last_prompt(self) -> str:
        """Get the last prompt sent to the model"""
        return self.call_history[-1] if self.call_history else ""
    
    def clear_history(self):
        """Clear call history"""
        self.call_history.clear()
        self.response_queue.clear()


class MockBigQueryClient:
    """Mock BigQuery client for testing"""
    
    def __init__(self):
        self.query_history = []
        self.mock_results = []
        self.should_fail = False
        self.failure_message = "Mock BigQuery error"
    
    def query(self, sql: str, **kwargs):
        """Mock query execution"""
        self.query_history.append(sql)
        
        if self.should_fail:
            raise Exception(self.failure_message)
        
        # Return mock results
        mock_job = Mock()
        mock_job.result.return_value = self.mock_results
        mock_job.total_rows = len(self.mock_results)
        
        return mock_job
    
    def set_mock_results(self, results: List[Dict]):
        """Set mock query results"""
        self.mock_results = [Mock(**result) for result in results]
    
    def set_failure(self, should_fail: bool, message: str = "Mock BigQuery error"):
        """Set whether queries should fail"""
        self.should_fail = should_fail
        self.failure_message = message
    
    def get_last_query(self) -> str:
        """Get the last executed query"""
        return self.query_history[-1] if self.query_history else ""


class TestDataBuilder:
    """Builder for creating test data"""
    
    @staticmethod
    def create_session_data(
        session_id: str = "test-session",
        title: str = "Test Session",
        message_count: int = 0
    ) -> Dict[str, Any]:
        """Create test session data"""
        return {
            "id": session_id,
            "title": title,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "message_count": message_count
        }
    
    @staticmethod
    def create_message_data(
        message_id: str = "test-msg",
        session_id: str = "test-session",
        content: str = "Test message",
        role: MessageRole = MessageRole.USER,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create test message data"""
        return {
            "id": message_id,
            "session_id": session_id,
            "content": content,
            "role": role.value,
            "timestamp": datetime.now(),
            "metadata": metadata
        }
    
    @staticmethod
    def create_conversation_data(
        session_id: str = "test-session",
        turns: int = 3
    ) -> Dict[str, Any]:
        """Create a complete conversation with multiple turns"""
        messages = []
        for i in range(turns):
            # User message
            messages.append(TestDataBuilder.create_message_data(
                message_id=f"user-msg-{i}",
                session_id=session_id,
                content=f"User message {i}",
                role=MessageRole.USER
            ))
            # Assistant message
            messages.append(TestDataBuilder.create_message_data(
                message_id=f"assistant-msg-{i}",
                session_id=session_id,
                content=f"Assistant response {i}",
                role=MessageRole.ASSISTANT
            ))
        
        return {
            "session": TestDataBuilder.create_session_data(
                session_id=session_id,
                message_count=len(messages)
            ),
            "messages": messages
        }
    
    @staticmethod
    def create_context_data(
        session_id: str = "test-session",
        last_query: str = "Test query",
        query_result: Optional[Dict] = None
    ) -> ToolContext:
        """Create test tool context"""
        context = ToolContext()
        context.update_state("session_id", session_id)
        context.update_state("last_query", last_query)
        
        if query_result is None:
            query_result = {
                "success": True,
                "data": [{"test": "data"}],
                "row_count": 1
            }
        
        context.update_state("query_result", query_result)
        return context
    
    @staticmethod
    def create_bigquery_result(
        data: List[Dict],
        success: bool = True,
        sql_query: str = "SELECT * FROM test_table"
    ) -> Dict[str, Any]:
        """Create mock BigQuery result"""
        return {
            "success": success,
            "data": data,
            "row_count": len(data),
            "sql_query": sql_query,
            "execution_time": 0.5
        }


class TestAssertions:
    """Custom assertions for testing"""
    
    @staticmethod
    def assert_valid_session(session_data: Dict[str, Any]):
        """Assert that session data is valid"""
        required_fields = ["id", "title", "created_at", "updated_at"]
        for field in required_fields:
            assert field in session_data, f"Session missing required field: {field}"
        
        assert len(session_data["id"]) > 0, "Session ID should not be empty"
        assert isinstance(session_data["created_at"], datetime), "created_at should be datetime"
    
    @staticmethod
    def assert_valid_message(message_data: Dict[str, Any]):
        """Assert that message data is valid"""
        required_fields = ["id", "session_id", "content", "role", "timestamp"]
        for field in required_fields:
            assert field in message_data, f"Message missing required field: {field}"
        
        assert message_data["role"] in ["user", "assistant"], f"Invalid role: {message_data['role']}"
        assert len(message_data["content"]) > 0, "Message content should not be empty"
    
    @staticmethod
    def assert_context_has_keys(context: ToolContext, expected_keys: List[str]):
        """Assert that context has expected keys"""
        # Use direct state access instead of get_state_keys()
        context_keys = list(context.state.keys())
        for key in expected_keys:
            assert key in context_keys, f"Context missing expected key: {key}"
    
    @staticmethod
    def assert_agent_response_valid(response: str):
        """Assert that agent response is valid"""
        assert isinstance(response, str), "Agent response should be string"
        assert len(response.strip()) > 0, "Agent response should not be empty"
        assert not response.startswith("ERROR"), "Agent response should not start with ERROR"
    
    @staticmethod
    def assert_chart_response(response: str):
        """Assert that response contains chart reference"""
        chart_indicators = ["/api/charts/", "![", "chart", "Chart"]
        has_chart = any(indicator in response for indicator in chart_indicators)
        assert has_chart, f"Response should contain chart reference: {response}"
    
    @staticmethod
    def assert_sql_query_valid(sql: str):
        """Assert that SQL query is valid"""
        sql_lower = sql.lower().strip()
        assert sql_lower.startswith("select"), "SQL should start with SELECT"
        assert "from" in sql_lower, "SQL should contain FROM clause"
        assert not any(keyword in sql_lower for keyword in ["drop", "delete", "update", "insert"]), \
            "SQL should not contain dangerous keywords"


class MockFileSystem:
    """Mock file system for testing file operations"""
    
    def __init__(self):
        self.files = {}
        self.directories = set()
    
    def create_file(self, path: str, content: str = ""):
        """Create a mock file"""
        self.files[path] = content
        # Create parent directories
        directory = os.path.dirname(path)
        if directory:
            self.directories.add(directory)
    
    def file_exists(self, path: str) -> bool:
        """Check if file exists"""
        return path in self.files
    
    def read_file(self, path: str) -> str:
        """Read file content"""
        if path not in self.files:
            raise FileNotFoundError(f"File not found: {path}")
        return self.files[path]
    
    def list_files(self, directory: str = "") -> List[str]:
        """List files in directory"""
        if directory:
            return [f for f in self.files.keys() if f.startswith(directory)]
        return list(self.files.keys())


class TestEnvironment:
    """Test environment management"""
    
    @staticmethod
    def setup_test_env():
        """Set up test environment variables"""
        test_env = {
            "TESTING": "true",
            "GOOGLE_API_KEY": "test-api-key",
            "GOOGLE_CLOUD_PROJECT": "test-project",
            "BIGQUERY_DATASET_ID": "test_dataset",
            "DATABASE_PATH": ":memory:",  # Use in-memory SQLite for tests
        }
        
        for key, value in test_env.items():
            os.environ[key] = value
    
    @staticmethod
    def cleanup_test_env():
        """Clean up test environment"""
        test_keys = [
            "TESTING", "GOOGLE_API_KEY", "GOOGLE_CLOUD_PROJECT",
            "BIGQUERY_DATASET_ID", "DATABASE_PATH"
        ]
        
        for key in test_keys:
            if key in os.environ:
                del os.environ[key]
    
    @staticmethod
    def create_temp_database() -> str:
        """Create temporary database for testing"""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)  # Close the file descriptor
        return path


class TestScenarios:
    """Pre-built test scenarios"""
    
    @staticmethod
    def employee_lookup_scenario():
        """Employee lookup conversation scenario"""
        return {
            "title": "Employee Lookup Test",
            "queries": [
                {
                    "query": "Where does Rosalinda Rodriguez work?",
                    "expected_agent": "call_db_agent",
                    "mock_result": {
                        "data": [{"location_code": "075", "location_name": "BUSINESS TECHNOLOGY DEPARTMENT"}]
                    },
                    "expected_response_contains": ["075", "BUSINESS TECHNOLOGY"]
                },
                {
                    "query": "Who else works here?",
                    "expected_agent": "call_db_agent",
                    "mock_result": {
                        "data": [
                            {"employee_name": "John Doe"},
                            {"employee_name": "Jane Smith"}
                        ]
                    },
                    "expected_response_contains": ["John Doe", "Jane Smith"]
                }
            ]
        }
    
    @staticmethod
    def chart_generation_scenario():
        """Chart generation conversation scenario"""
        return {
            "title": "Chart Generation Test",
            "queries": [
                {
                    "query": "Show me sales by category in a bar chart",
                    "expected_agents": ["call_db_agent", "call_analytics_agent"],
                    "mock_result": {
                        "data": [
                            {"category": "Electronics", "sales": 50000},
                            {"category": "Clothing", "sales": 30000}
                        ]
                    },
                    "expected_response_contains": ["/api/charts/", "chart"]
                }
            ]
        }
    
    @staticmethod
    def error_handling_scenario():
        """Error handling conversation scenario"""
        return {
            "title": "Error Handling Test",
            "queries": [
                {
                    "query": "Invalid query that will fail",
                    "expected_agent": "call_db_agent",
                    "should_fail": True,
                    "failure_message": "Database connection failed",
                    "expected_response_contains": ["error", "sorry"]
                }
            ]
        }