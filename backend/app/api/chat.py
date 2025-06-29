from fastapi import APIRouter, HTTPException
from app.models.chat import SendMessageRequest, SendMessageResponse, ChatHistoryResponse, MessageRole
from app.data_science.agent import root_agent as data_science_agent
import logging

# Import the persistent session manager
from app.core.persistent_session_manager import persistent_session_manager as session_manager

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
                # Create session with the requested ID
                session = session_manager.create_session(session_id=session_id)
        
        # Add user message
        user_message = session_manager.add_message(
            session_id=session_id,
            content=request.message,
            role=MessageRole.USER
        )
        
        # Get response from Data Science Multi-Agent System
        from app.data_science.tools import ToolContext
        context = ToolContext()
        context.update_state("session_id", session_id)
        context.update_state("message_history", [msg.content for msg in session.messages[-5:]])
        
        # Get memory from persistent session manager
        memory = session_manager.get_session_memory(session_id)
        if memory:
            # Transfer memory state to ToolContext
            for key, value in memory.state.items():
                context.update_state(key, value)
            context.history = memory.history
        
        ai_response = await data_science_agent.process_message(request.message, context)
        
        # Save updated context back to persistent memory
        if memory:
            for key, value in context.state.items():
                memory.update_state(key, value)
            memory.history = context.history
        
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

@router.get("/chat/context/{session_id}")
async def get_session_context(session_id: str):
    """Get the full context for a session including entities and query results"""
    try:
        context = session_manager.get_conversation_context(session_id)
        return context
    except Exception as e:
        logger.error(f"Error getting session context: {e}")
        raise HTTPException(status_code=500, detail=str(e))