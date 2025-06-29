"""
Database management API endpoints
"""

from fastapi import APIRouter, HTTPException
from app.database.models import db_manager
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/database/stats")
async def get_database_stats():
    """Get database statistics"""
    try:
        with db_manager.get_connection() as conn:
            # Count sessions
            session_count = conn.execute("SELECT COUNT(*) FROM chat_sessions").fetchone()[0]
            
            # Count messages
            message_count = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
            
            # Count sessions with memory
            memory_count = conn.execute("SELECT COUNT(*) FROM session_memory").fetchone()[0]
            
            # Get recent sessions
            recent_sessions = conn.execute("""
                SELECT id, title, datetime(updated_at) as updated_at 
                FROM chat_sessions 
                ORDER BY updated_at DESC 
                LIMIT 10
            """).fetchall()
            
            return {
                "session_count": session_count,
                "message_count": message_count,
                "memory_count": memory_count,
                "recent_sessions": [dict(row) for row in recent_sessions]
            }
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/database/cleanup")
async def cleanup_old_sessions(days_old: int = 30):
    """Clean up sessions older than specified days"""
    try:
        deleted_count = db_manager.cleanup_old_sessions(days_old)
        return {
            "message": f"Cleaned up {deleted_count} sessions older than {days_old} days",
            "deleted_count": deleted_count
        }
    except Exception as e:
        logger.error(f"Error cleaning up sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/database/session/{session_id}/full")
async def get_full_session_data(session_id: str):
    """Get complete session data including messages and memory"""
    try:
        # Get session
        session = db_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get messages
        messages = db_manager.get_messages(session_id)
        
        # Get memory
        memory = db_manager.get_session_memory(session_id)
        
        return {
            "session": session,
            "messages": messages,
            "memory": memory,
            "message_count": len(messages)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting full session data: {e}")
        raise HTTPException(status_code=500, detail=str(e))