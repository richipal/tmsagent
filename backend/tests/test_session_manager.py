"""
Tests for persistent session manager
"""

import pytest
from datetime import datetime
from app.models.chat import MessageRole
from app.data_science.tools import ToolContext


class TestPersistentSessionManager:
    """Test PersistentSessionManager functionality"""
    
    def test_create_session_without_id(self, test_session_manager):
        """Test creating a session without providing an ID"""
        session = test_session_manager.create_session(title="Test Session")
        
        assert session.id is not None
        assert len(session.id) == 36  # UUID format
        assert session.title == "Test Session"
        assert isinstance(session.created_at, datetime)
        assert len(session.messages) == 0
    
    def test_create_session_with_id(self, test_session_manager):
        """Test creating a session with a specific ID"""
        custom_id = "custom-session-123"
        session = test_session_manager.create_session(
            title="Custom Session", 
            session_id=custom_id
        )
        
        assert session.id == custom_id
        assert session.title == "Custom Session"
    
    def test_get_existing_session(self, test_session_manager):
        """Test retrieving an existing session"""
        # Create session
        session = test_session_manager.create_session(title="Test Session")
        session_id = session.id
        
        # Add some messages
        test_session_manager.add_message(
            session_id, "Hello", MessageRole.USER
        )
        test_session_manager.add_message(
            session_id, "Hi there!", MessageRole.ASSISTANT
        )
        
        # Retrieve session
        retrieved = test_session_manager.get_session(session_id)
        assert retrieved is not None
        assert retrieved.id == session_id
        assert retrieved.title == "Test Session"
        assert len(retrieved.messages) == 2
        assert retrieved.messages[0].content == "Hello"
        assert retrieved.messages[1].content == "Hi there!"
    
    def test_session_memory_persistence(self, test_session_manager):
        """Test that session memory persists correctly"""
        session = test_session_manager.create_session(title="Memory Test")
        session_id = session.id
        
        # Get memory and update it
        memory = test_session_manager.get_session_memory(session_id)
        assert memory is not None
        
        memory.update_state("last_query", "Where does John work?")
        memory.update_state("last_response", "Engineering")
        memory.update_state("query_result", {"department": "Engineering"})
        memory.add_to_history("database", "Where does John work?", "Engineering")
        
        # Create new session manager instance to test persistence
        new_manager = test_session_manager.__class__()
        new_memory = new_manager.get_session_memory(session_id)
        
        assert new_memory is not None
        assert new_memory.get_state("last_query") == "Where does John work?"
        assert new_memory.get_state("last_response") == "Engineering"
        assert new_memory.get_state("query_result")["department"] == "Engineering"
        assert len(new_memory.history) == 1
        assert new_memory.history[0]["agent"] == "database"
    
    def test_add_message_with_metadata(self, test_session_manager):
        """Test adding messages with metadata"""
        session = test_session_manager.create_session(title="Metadata Test")
        session_id = session.id
        
        # Add message with metadata
        metadata = {"has_chart": True, "confidence": 0.95}
        message = test_session_manager.add_message(
            session_id, 
            "Here is a chart", 
            MessageRole.ASSISTANT,
            metadata=metadata
        )
        
        assert message.id is not None
        assert message.content == "Here is a chart"
        assert message.role == MessageRole.ASSISTANT
        
        # Retrieve and verify
        retrieved = test_session_manager.get_messages(session_id)
        assert len(retrieved) == 1
        # Note: metadata is stored in DB but not on Message model
    
    def test_memory_cache(self, test_session_manager):
        """Test that memory cache works correctly"""
        session = test_session_manager.create_session(title="Cache Test")
        session_id = session.id
        
        # First access creates memory
        memory1 = test_session_manager.get_session_memory(session_id)
        memory1.update_state("test", "value1")
        
        # Second access should return same instance (cached)
        memory2 = test_session_manager.get_session_memory(session_id)
        assert memory2.get_state("test") == "value1"
        assert memory1 is memory2  # Same object reference
    
    def test_delete_session_clears_cache(self, test_session_manager):
        """Test that deleting a session clears its cache"""
        session = test_session_manager.create_session(title="Delete Test")
        session_id = session.id
        
        # Access memory to cache it
        memory = test_session_manager.get_session_memory(session_id)
        memory.update_state("test", "value")
        
        # Delete session
        deleted = test_session_manager.delete_session(session_id)
        assert deleted is True
        
        # Verify cache is cleared
        assert session_id not in test_session_manager._memory_cache
        
        # Verify session is deleted
        assert test_session_manager.get_session(session_id) is None
        assert test_session_manager.get_session_memory(session_id) is None
    
    def test_list_sessions_without_messages(self, test_session_manager):
        """Test that listing sessions doesn't load all messages"""
        # Create sessions with messages
        for i in range(3):
            session = test_session_manager.create_session(title=f"Session {i}")
            # Add many messages
            for j in range(10):
                test_session_manager.add_message(
                    session.id, f"Message {j}", MessageRole.USER
                )
        
        # List sessions
        sessions = test_session_manager.list_sessions()
        assert len(sessions) >= 3
        
        # Verify messages are not loaded (performance optimization)
        for session in sessions:
            assert len(session.messages) == 0
    
    def test_get_conversation_context(self, test_session_manager):
        """Test getting comprehensive conversation context"""
        session = test_session_manager.create_session(title="Context Test")
        session_id = session.id
        
        # Add messages
        test_session_manager.add_message(
            session_id, "Where does Rosalinda work?", MessageRole.USER
        )
        test_session_manager.add_message(
            session_id, "075: BUSINESS TECHNOLOGY", MessageRole.ASSISTANT
        )
        test_session_manager.add_message(
            session_id, "Who else works there?", MessageRole.USER
        )
        test_session_manager.add_message(
            session_id, "John, Jane, and Bob", MessageRole.ASSISTANT
        )
        
        # Update memory
        memory = test_session_manager.get_session_memory(session_id)
        memory.update_state("last_query", "Who else works there?")
        memory.update_state("last_response", "John, Jane, and Bob")
        memory.update_state("query_result", {"employees": ["John", "Jane", "Bob"]})
        
        # Get context
        context = test_session_manager.get_conversation_context(session_id)
        
        assert context["session_id"] == session_id
        assert context["message_count"] == 4
        assert len(context["message_history"]) == 4
        assert len(context["full_conversation"]) == 2
        assert context["memory_state"]["last_query"] == "Who else works there?"
        assert context["last_query_result"]["employees"] == ["John", "Jane", "Bob"]
    
    def test_cleanup_old_sessions(self, test_session_manager):
        """Test cleanup functionality"""
        # Create sessions
        session1 = test_session_manager.create_session(title="Session 1")
        session2 = test_session_manager.create_session(title="Session 2")
        
        # Cache some memory
        memory1 = test_session_manager.get_session_memory(session1.id)
        memory1.update_state("test", "value")
        
        # Run cleanup (with 0 days to clean everything for test)
        deleted_count = test_session_manager.cleanup_old_sessions(days_old=0)
        
        # Verify cache is cleared
        assert len(test_session_manager._memory_cache) == 0
        
        # Note: actual deletion count depends on DB implementation