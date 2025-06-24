"""
Integration Tests for API endpoints
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import json
import tempfile
import os


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    import sys
    from pathlib import Path
    
    # Add backend to Python path
    backend_path = Path(__file__).parent.parent / "backend"
    sys.path.insert(0, str(backend_path))
    
    from main import app
    return TestClient(app)


@pytest.mark.integration
def test_health_endpoint(test_client):
    """Test the health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.integration
def test_root_endpoint(test_client):
    """Test the root endpoint."""
    response = test_client.get("/")
    assert response.status_code == 200
    assert "ADK Data Science Chatbot API" in response.json()["message"]


@pytest.mark.integration
@patch('app.data_science.agent.root_agent.process_message')
async def test_chat_send_endpoint(mock_process_message, test_client):
    """Test the chat send endpoint."""
    mock_process_message.return_value = "Test response from agent"
    
    response = test_client.post(
        "/api/chat/send",
        json={"message": "Hello, test message"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "session_id" in data
    assert "message_id" in data


@pytest.mark.integration
def test_chat_send_with_session_id(test_client):
    """Test chat send with existing session ID."""
    # First, create a session
    response1 = test_client.post(
        "/api/chat/send",
        json={"message": "First message"}
    )
    assert response1.status_code == 200
    session_id = response1.json()["session_id"]
    
    # Send another message with the same session
    response2 = test_client.post(
        "/api/chat/send",
        json={"message": "Second message", "session_id": session_id}
    )
    assert response2.status_code == 200
    assert response2.json()["session_id"] == session_id


@pytest.mark.integration
def test_chat_history_endpoint(test_client):
    """Test the chat history endpoint."""
    # First, send a message to create history
    response1 = test_client.post(
        "/api/chat/send",
        json={"message": "Test message for history"}
    )
    session_id = response1.json()["session_id"]
    
    # Get chat history
    response2 = test_client.get(f"/api/chat/history/{session_id}")
    assert response2.status_code == 200
    data = response2.json()
    assert "messages" in data
    assert "session_id" in data
    assert len(data["messages"]) >= 1


@pytest.mark.integration
def test_list_sessions_endpoint(test_client):
    """Test the list sessions endpoint."""
    response = test_client.get("/api/chat/sessions")
    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert isinstance(data["sessions"], list)


@pytest.mark.integration
def test_delete_session_endpoint(test_client):
    """Test the delete session endpoint."""
    # Create a session first
    response1 = test_client.post(
        "/api/chat/send",
        json={"message": "Test message"}
    )
    session_id = response1.json()["session_id"]
    
    # Delete the session
    response2 = test_client.delete(f"/api/chat/session/{session_id}")
    assert response2.status_code == 200
    assert "deleted successfully" in response2.json()["message"]


@pytest.mark.integration
def test_delete_nonexistent_session(test_client):
    """Test deleting a non-existent session."""
    response = test_client.delete("/api/chat/session/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.integration
def test_file_upload_endpoint(test_client):
    """Test the file upload endpoint."""
    # Create a temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("customer_id,product_id,quantity,price\n")
        f.write("1,A001,2,29.99\n")
        f.write("2,B002,1,15.50\n")
        temp_file_path = f.name
    
    try:
        with open(temp_file_path, 'rb') as f:
            response = test_client.post(
                "/api/upload",
                files={"file": ("test.csv", f, "text/csv")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "file_id" in data
        assert "filename" in data
        assert "status" in data
        assert data["status"] == "completed"
    finally:
        os.unlink(temp_file_path)


@pytest.mark.integration
def test_file_upload_invalid_type(test_client):
    """Test file upload with invalid file type."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is not a valid data file")
        temp_file_path = f.name
    
    try:
        with open(temp_file_path, 'rb') as f:
            response = test_client.post(
                "/api/upload",
                files={"file": ("test.txt", f, "text/plain")}
            )
        
        # Should reject invalid file type
        assert response.status_code == 400
    finally:
        os.unlink(temp_file_path)


@pytest.mark.integration
def test_export_chat_json(test_client):
    """Test chat export in JSON format."""
    # Create a session with messages
    response1 = test_client.post(
        "/api/chat/send",
        json={"message": "Test message for export"}
    )
    session_id = response1.json()["session_id"]
    
    # Export the chat
    response2 = test_client.get(f"/api/export/{session_id}?format=json")
    assert response2.status_code == 200
    assert "application/json" in response2.headers["content-type"]


@pytest.mark.integration
def test_export_chat_csv(test_client):
    """Test chat export in CSV format."""
    # Create a session with messages
    response1 = test_client.post(
        "/api/chat/send",
        json={"message": "Test message for CSV export"}
    )
    session_id = response1.json()["session_id"]
    
    # Export the chat as CSV
    response2 = test_client.get(f"/api/export/{session_id}?format=csv")
    assert response2.status_code == 200
    assert "text/csv" in response2.headers["content-type"]


@pytest.mark.integration
def test_export_chat_txt(test_client):
    """Test chat export in TXT format."""
    # Create a session with messages
    response1 = test_client.post(
        "/api/chat/send",
        json={"message": "Test message for TXT export"}
    )
    session_id = response1.json()["session_id"]
    
    # Export the chat as TXT
    response2 = test_client.get(f"/api/export/{session_id}?format=txt")
    assert response2.status_code == 200
    assert "text/plain" in response2.headers["content-type"]


@pytest.mark.integration
def test_export_invalid_format(test_client):
    """Test chat export with invalid format."""
    # Create a session first
    response1 = test_client.post(
        "/api/chat/send",
        json={"message": "Test message"}
    )
    session_id = response1.json()["session_id"]
    
    # Try to export with invalid format
    response2 = test_client.get(f"/api/export/{session_id}?format=invalid")
    assert response2.status_code == 400


@pytest.mark.integration
def test_file_info_endpoint(test_client):
    """Test getting file information."""
    # First upload a file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("test,data\n1,2\n")
        temp_file_path = f.name
    
    try:
        with open(temp_file_path, 'rb') as f:
            upload_response = test_client.post(
                "/api/upload",
                files={"file": ("test.csv", f, "text/csv")}
            )
        
        file_id = upload_response.json()["file_id"]
        
        # Get file info
        info_response = test_client.get(f"/api/file/{file_id}")
        assert info_response.status_code == 200
        data = info_response.json()
        assert "file_id" in data
        assert "filename" in data
        assert "size" in data
    finally:
        os.unlink(temp_file_path)


@pytest.mark.integration
def test_get_nonexistent_file_info(test_client):
    """Test getting info for non-existent file."""
    response = test_client.get("/api/file/nonexistent-id")
    assert response.status_code == 404