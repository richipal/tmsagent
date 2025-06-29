"""
Persistent Session Manager using SQLite for conversation storage
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from app.models.chat import ChatSession, Message, MessageRole
from app.data_science.tools import ToolContext
from app.database.models import db_manager


class PersistentSessionMemory:
    """Session memory that syncs with SQLite database"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state = {}
        self.history = []
        self._load_from_db()
    
    def _load_from_db(self):
        """Load memory from database"""
        memory_data = db_manager.get_session_memory(self.session_id)
        if memory_data:
            self.state = memory_data['context_state']
            self.history = memory_data['history']
    
    def update_state(self, key: str, value: Any):
        """Update state and persist to database"""
        self.state[key] = value
        self._save_to_db()
    
    def get_state(self, key: str, default=None):
        """Get value from state"""
        return self.state.get(key, default)
    
    def add_to_history(self, agent: str, query: str, response: str):
        """Add to history and persist to database"""
        self.history.append({
            "agent": agent,
            "query": query,
            "response": response,
            "timestamp": datetime.now().isoformat()
        })
        self._save_to_db()
    
    def _save_to_db(self):
        """Save current state to database"""
        db_manager.save_session_memory(self.session_id, self.state, self.history)


class PersistentSessionManager:
    """Session manager with SQLite persistence"""
    
    def __init__(self):
        self._memory_cache = {}  # In-memory cache for performance
    
    def create_session(self, title: str = None, session_id: str = None) -> ChatSession:
        """Create a new chat session"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        now = datetime.now()
        
        if not title:
            title = f"Chat {now.strftime('%Y-%m-%d %H:%M')}"
        
        # Create in database
        db_session = db_manager.create_session(session_id, title)
        
        # Create ChatSession object
        session = ChatSession(
            id=session_id,
            title=title,
            messages=[],
            created_at=now,
            updated_at=now
        )
        
        return session
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get session by ID"""
        db_session = db_manager.get_session(session_id)
        if not db_session:
            return None
        
        # Get messages from database
        db_messages = db_manager.get_messages(session_id)
        
        # Convert to Message objects
        messages = []
        for db_msg in db_messages:
            message = Message(
                id=db_msg['id'],
                content=db_msg['content'],
                role=MessageRole(db_msg['role']),
                timestamp=datetime.fromisoformat(db_msg['timestamp']),
                session_id=db_msg['session_id']
            )
            messages.append(message)
        
        # Create ChatSession object
        session = ChatSession(
            id=db_session['id'],
            title=db_session['title'],
            messages=messages,
            created_at=datetime.fromisoformat(db_session['created_at']),
            updated_at=datetime.fromisoformat(db_session['updated_at'])
        )
        
        return session
    
    def get_session_memory(self, session_id: str) -> Optional[PersistentSessionMemory]:
        """Get or create session memory"""
        if session_id not in self._memory_cache:
            # Check if session exists
            if db_manager.get_session(session_id):
                self._memory_cache[session_id] = PersistentSessionMemory(session_id)
            else:
                return None
        
        return self._memory_cache[session_id]
    
    def add_message(self, session_id: str, content: str, role: MessageRole, 
                   metadata: Optional[Dict[str, Any]] = None) -> Message:
        """Add message to session"""
        # Verify session exists
        if not db_manager.get_session(session_id):
            raise ValueError(f"Session {session_id} not found")
        
        message_id = str(uuid.uuid4())
        
        # Add to database
        db_message = db_manager.add_message(
            message_id, session_id, content, role.value, metadata
        )
        
        # Create Message object
        message = Message(
            id=message_id,
            content=content,
            role=role,
            timestamp=db_message['timestamp'],
            session_id=session_id
        )
        
        # Update session memory if it's an assistant response
        if role == MessageRole.ASSISTANT:
            memory = self.get_session_memory(session_id)
            if memory:
                memory.add_to_history("assistant", "", content)
        
        return message
    
    def get_messages(self, session_id: str) -> List[Message]:
        """Get all messages for a session"""
        db_messages = db_manager.get_messages(session_id)
        
        messages = []
        for db_msg in db_messages:
            message = Message(
                id=db_msg['id'],
                content=db_msg['content'],
                role=MessageRole(db_msg['role']),
                timestamp=datetime.fromisoformat(db_msg['timestamp']),
                session_id=db_msg['session_id']
            )
            messages.append(message)
        
        return messages
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session and all related data"""
        # Remove from memory cache
        if session_id in self._memory_cache:
            del self._memory_cache[session_id]
        
        # Delete from database
        return db_manager.delete_session(session_id)
    
    def update_session_title(self, session_id: str, title: str) -> bool:
        """Update session title"""
        return db_manager.update_session_title(session_id, title)
    
    def list_sessions(self) -> List[ChatSession]:
        """List all sessions"""
        db_sessions = db_manager.list_sessions()
        
        sessions = []
        for db_session in db_sessions:
            session = ChatSession(
                id=db_session['id'],
                title=db_session['title'],
                messages=[],  # Don't load messages for list view (performance)
                created_at=datetime.fromisoformat(db_session['created_at']),
                updated_at=datetime.fromisoformat(db_session['updated_at'])
            )
            sessions.append(session)
        
        return sessions
    
    def get_conversation_context(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive conversation context"""
        session = self.get_session(session_id)
        memory = self.get_session_memory(session_id)
        
        if not session or not memory:
            return {}
        
        # Build conversation pairs
        messages = session.messages
        conversation_pairs = []
        for i in range(0, len(messages), 2):
            if i < len(messages) - 1:
                conversation_pairs.append({
                    "user": messages[i].content if messages[i].role == MessageRole.USER else messages[i+1].content,
                    "assistant": messages[i+1].content if messages[i+1].role == MessageRole.ASSISTANT else messages[i].content
                })
        
        return {
            "session_id": session_id,
            "message_history": [msg.content for msg in messages],
            "full_conversation": conversation_pairs,
            "memory_state": memory.state,
            "memory_history": memory.history,
            "message_count": len(messages),
            "last_query_result": memory.get_state("query_result"),
            "last_db_output": memory.get_state("db_agent_output"),
            "last_analytics_output": memory.get_state("ds_agent_output")
        }
    
    def cleanup_old_sessions(self, days_old: int = 30):
        """Clean up old sessions"""
        # Clear memory cache for deleted sessions
        deleted_count = db_manager.cleanup_old_sessions(days_old)
        
        # Clear memory cache (will be rebuilt as needed)
        self._memory_cache.clear()
        
        return deleted_count


# Global persistent session manager instance
persistent_session_manager = PersistentSessionManager()