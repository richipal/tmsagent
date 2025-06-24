import uuid
from datetime import datetime
from typing import Dict, List, Optional
from app.models.chat import ChatSession, Message, MessageRole

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}
    
    def create_session(self, title: str = None) -> ChatSession:
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        if not title:
            title = f"Chat {now.strftime('%Y-%m-%d %H:%M')}"
        
        session = ChatSession(
            id=session_id,
            title=title,
            messages=[],
            created_at=now,
            updated_at=now
        )
        
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        return self.sessions.get(session_id)
    
    def add_message(self, session_id: str, content: str, role: MessageRole) -> Message:
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        message = Message(
            id=str(uuid.uuid4()),
            content=content,
            role=role,
            timestamp=datetime.now(),
            session_id=session_id
        )
        
        session.messages.append(message)
        session.updated_at = datetime.now()
        
        return message
    
    def get_messages(self, session_id: str) -> List[Message]:
        session = self.get_session(session_id)
        return session.messages if session else []
    
    def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def list_sessions(self) -> List[ChatSession]:
        return list(self.sessions.values())

session_manager = SessionManager()