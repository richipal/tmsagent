from fastapi import APIRouter, HTTPException
from app.models.chat import SendMessageRequest, SendMessageResponse, ChatHistoryResponse, MessageRole
from app.core.session_manager import session_manager
from app.data_science.agent import root_agent as data_science_agent
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/chat/send", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest):
    """Send a message to the Data Science Multi-Agent System and get a response"""
    try:
        # Create session if not provided
        if not request.session_id:
            session = session_manager.create_session()
            session_id = session.id
        else:
            session_id = request.session_id
            session = session_manager.get_session(session_id)
            if not session:
                session = session_manager.create_session()
                session_id = session.id
        
        # Add user message
        user_message = session_manager.add_message(
            session_id=session_id,
            content=request.message,
            role=MessageRole.USER
        )
        
        # Get response from Data Science Multi-Agent System
        # Pass session context for better continuity
        session_context = {
            "session_id": session_id,
            "message_history": [msg.content for msg in session.messages[-5:]]  # Last 5 messages for context
        }
        ai_response = await data_science_agent.process_message(request.message, session_context)
        
        # Add AI message
        ai_message = session_manager.add_message(
            session_id=session_id,
            content=ai_response,
            role=MessageRole.ASSISTANT
        )
        
        return SendMessageResponse(
            message=ai_response,
            session_id=session_id,
            message_id=ai_message.id
        )
        
    except Exception as e:
        logger.error(f"Error in send_message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    try:
        messages = session_manager.get_messages(session_id)
        return ChatHistoryResponse(
            messages=messages,
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/chat/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session"""
    try:
        success = session_manager.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"message": "Session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/sessions")
async def list_sessions():
    """List all chat sessions"""
    try:
        sessions = session_manager.list_sessions()
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))