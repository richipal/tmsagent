"""
Very basic functionality tests that should always work
"""

import pytest
import os
import tempfile
from datetime import datetime

# Set test environment
os.environ["TESTING"] = "true"
os.environ["GOOGLE_API_KEY"] = "test-api-key"
os.environ["GOOGLE_CLOUD_PROJECT"] = "test-project"

def test_python_basic():
    """Test basic Python functionality"""
    assert 1 + 1 == 2
    assert "hello".upper() == "HELLO"
    
def test_sqlite_works():
    """Test SQLite works"""
    import sqlite3
    
    # Create in-memory database
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    
    cursor.execute("CREATE TABLE test (id INTEGER, name TEXT)")
    cursor.execute("INSERT INTO test VALUES (1, 'hello')")
    
    cursor.execute("SELECT * FROM test")
    row = cursor.fetchone()
    
    assert row[0] == 1
    assert row[1] == "hello"
    
    conn.close()

def test_imports_work():
    """Test basic imports"""
    # These should always work
    import json
    import datetime
    from typing import Dict, List
    
    # Test pydantic
    try:
        from pydantic import BaseModel
        
        class TestModel(BaseModel):
            name: str
            value: int
            
        model = TestModel(name="test", value=42)
        assert model.name == "test"
        assert model.value == 42
        
    except ImportError:
        pytest.skip("Pydantic not available")

def test_toolcontext_minimal():
    """Test ToolContext with minimal functionality"""
    try:
        from app.data_science.tools import ToolContext
        
        # Create context
        context = ToolContext()
        
        # Test basic state operations
        context.update_state("test", "value")
        assert context.get_state("test") == "value"
        assert context.get_state("nonexistent") is None
        assert context.get_state("nonexistent", "default") == "default"
        
        # Test history
        assert hasattr(context, 'history')
        assert isinstance(context.history, list)
        
        # Test state attribute
        assert hasattr(context, 'state')
        assert isinstance(context.state, dict)
        assert "test" in context.state
        
    except ImportError:
        pytest.skip("ToolContext not available")

@pytest.mark.asyncio
async def test_async_works():
    """Test async functionality"""
    import asyncio
    
    async def simple_async():
        await asyncio.sleep(0.001)
        return "async_result"
    
    result = await simple_async()
    assert result == "async_result"