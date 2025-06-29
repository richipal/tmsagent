"""
Tests for database models and persistence
"""

import pytest
from datetime import datetime, timedelta
import json


class TestDatabaseManager:
    """Test DatabaseManager functionality"""
    
    def test_init_database(self, test_db_manager):
        """Test database initialization creates required tables"""
        with test_db_manager.get_connection() as conn:
            # Check tables exist
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('chat_sessions', 'messages', 'session_memory')
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            assert 'chat_sessions' in tables
            assert 'messages' in tables
            assert 'session_memory' in tables
    
    def test_create_session(self, test_db_manager):
        """Test creating a new session"""
        session_id = "test-session-1"
        title = "Test Session"
        
        session = test_db_manager.create_session(session_id, title)
        
        assert session['id'] == session_id
        assert session['title'] == title
        assert isinstance(session['created_at'], datetime)
        assert isinstance(session['updated_at'], datetime)
        
        # Verify in database
        retrieved = test_db_manager.get_session(session_id)
        assert retrieved is not None
        assert retrieved['id'] == session_id
        assert retrieved['title'] == title
    
    def test_get_nonexistent_session(self, test_db_manager):
        """Test getting a session that doesn't exist"""
        session = test_db_manager.get_session("nonexistent-id")
        assert session is None
    
    def test_add_message(self, test_db_manager):
        """Test adding messages to a session"""
        # Create session first
        session_id = "test-session-2"
        test_db_manager.create_session(session_id, "Test Session")
        
        # Add messages
        msg1 = test_db_manager.add_message(
            "msg-1", session_id, "Hello, how are you?", "user"
        )
        msg2 = test_db_manager.add_message(
            "msg-2", session_id, "I'm doing well, thank you!", "assistant",
            metadata={"confidence": 0.95}
        )
        
        # Retrieve messages
        messages = test_db_manager.get_messages(session_id)
        assert len(messages) == 2
        
        assert messages[0]['id'] == "msg-1"
        assert messages[0]['content'] == "Hello, how are you?"
        assert messages[0]['role'] == "user"
        assert messages[0]['metadata'] is None
        
        assert messages[1]['id'] == "msg-2"
        assert messages[1]['content'] == "I'm doing well, thank you!"
        assert messages[1]['role'] == "assistant"
        assert messages[1]['metadata']['confidence'] == 0.95
    
    def test_save_and_get_session_memory(self, test_db_manager):
        """Test saving and retrieving session memory"""
        session_id = "test-session-3"
        test_db_manager.create_session(session_id, "Test Session")
        
        context_state = {
            "last_query": "Where does John work?",
            "last_response": "Engineering Department",
            "query_result": {"data": [{"department": "Engineering"}]}
        }
        
        history = [
            {"agent": "database", "query": "Where does John work?", 
             "response": "Engineering Department", "timestamp": "2024-01-01T10:00:00"}
        ]
        
        # Save memory
        test_db_manager.save_session_memory(session_id, context_state, history)
        
        # Retrieve memory
        memory = test_db_manager.get_session_memory(session_id)
        assert memory is not None
        assert memory['session_id'] == session_id
        assert memory['context_state']['last_query'] == "Where does John work?"
        assert memory['context_state']['query_result']['data'][0]['department'] == "Engineering"
        assert len(memory['history']) == 1
        assert memory['history'][0]['agent'] == "database"
    
    def test_update_session_memory(self, test_db_manager):
        """Test updating existing session memory"""
        session_id = "test-session-4"
        test_db_manager.create_session(session_id, "Test Session")
        
        # Initial save
        test_db_manager.save_session_memory(
            session_id, 
            {"count": 1}, 
            [{"event": "first"}]
        )
        
        # Update
        test_db_manager.save_session_memory(
            session_id, 
            {"count": 2, "new_key": "new_value"}, 
            [{"event": "first"}, {"event": "second"}]
        )
        
        # Verify update
        memory = test_db_manager.get_session_memory(session_id)
        assert memory['context_state']['count'] == 2
        assert memory['context_state']['new_key'] == "new_value"
        assert len(memory['history']) == 2
    
    def test_delete_session(self, test_db_manager):
        """Test deleting a session and cascade deletion"""
        session_id = "test-session-5"
        test_db_manager.create_session(session_id, "Test Session")
        test_db_manager.add_message("msg-1", session_id, "Test message", "user")
        test_db_manager.save_session_memory(session_id, {"test": "data"}, [])
        
        # Verify data exists
        assert test_db_manager.get_session(session_id) is not None
        assert len(test_db_manager.get_messages(session_id)) == 1
        assert test_db_manager.get_session_memory(session_id) is not None
        
        # Delete session
        deleted = test_db_manager.delete_session(session_id)
        assert deleted is True
        
        # Verify cascade deletion
        assert test_db_manager.get_session(session_id) is None
        assert len(test_db_manager.get_messages(session_id)) == 0
        assert test_db_manager.get_session_memory(session_id) is None
    
    def test_list_sessions(self, test_db_manager):
        """Test listing sessions ordered by most recent"""
        # Create sessions with different timestamps
        test_db_manager.create_session("session-1", "First Session")
        test_db_manager.create_session("session-2", "Second Session")
        test_db_manager.create_session("session-3", "Third Session")
        
        # Update session 1 to make it most recent
        test_db_manager.update_session("session-1")
        
        sessions = test_db_manager.list_sessions()
        assert len(sessions) >= 3
        
        # Verify order (most recent first)
        session_ids = [s['id'] for s in sessions[:3]]
        assert session_ids[0] == "session-1"  # Most recently updated
    
    def test_cleanup_old_sessions(self, test_db_manager):
        """Test cleaning up old sessions"""
        # Create an old session
        old_session_id = "old-session"
        test_db_manager.create_session(old_session_id, "Old Session")
        
        # Manually update the timestamp to be old
        old_date = datetime.now() - timedelta(days=40)
        with test_db_manager.get_connection() as conn:
            conn.execute("""
                UPDATE chat_sessions 
                SET updated_at = ? 
                WHERE id = ?
            """, (old_date, old_session_id))
        
        # Create a recent session
        recent_session_id = "recent-session"
        test_db_manager.create_session(recent_session_id, "Recent Session")
        
        # Cleanup sessions older than 30 days
        deleted_count = test_db_manager.cleanup_old_sessions(days_old=30)
        assert deleted_count == 1
        
        # Verify old session is deleted, recent session remains
        assert test_db_manager.get_session(old_session_id) is None
        assert test_db_manager.get_session(recent_session_id) is not None