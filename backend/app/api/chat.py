from fastapi import APIRouter, HTTPException, Request
from app.models.chat import SendMessageRequest, SendMessageResponse, ChatHistoryResponse, MessageRole, UpdateSessionTitleRequest
from app.data_science.agent import root_agent as data_science_agent
import logging
import time

# Import the persistent session manager
from app.core.persistent_session_manager import persistent_session_manager as session_manager

# Import observability
from app.config.observability import observability

# Import authentication
from app.middleware.auth_middleware import get_current_user, get_user_id
from app.database.models import db_manager

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/chat/send", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest, http_request: Request):
    """Send a message to the Data Science Multi-Agent System and get a response"""
    try:
        print("=== Chat send message endpoint called ===")
        # Get authenticated user
        user = get_current_user(http_request)
        user_id = get_user_id(http_request)
        
        print(f"Chat: User from middleware: {user.email if user else 'None'}")
        print(f"Chat: User ID: {user_id}")
        
        # Update or create user record if authenticated
        if user:
            print(f"Chat: Creating/updating user record for {user.email}")
            try:
                db_manager.create_or_update_user(
                    user_id=user.id,
                    email=user.email,
                    name=user.name,
                picture=user.picture,
                verified_email=user.verified_email
            )
                print("Chat: User record created/updated successfully")
            except Exception as e:
                print(f"Chat: Error creating/updating user record: {e}")
                import traceback
                traceback.print_exc()
        
        # Create session if not provided
        if not request.session_id:
            session = session_manager.create_session(user_id=user_id)
            session_id = session.id
        else:
            session_id = request.session_id
            session = session_manager.get_session(session_id)
            if not session:
                # Create session with the requested ID
                session = session_manager.create_session(session_id=session_id, user_id=user_id)
            else:
                # Verify session belongs to user (for security)
                if hasattr(session, 'user_id') and session.user_id != user_id:
                    raise HTTPException(status_code=403, detail="Access denied to this session")
        
        # Ensure we have a valid session
        if not session:
            raise HTTPException(status_code=500, detail="Failed to create or retrieve session")
        
        # Add user message
        user_message = session_manager.add_message(
            session_id=session_id,
            content=request.message,
            role=MessageRole.USER
        )
        
        # Track user query
        start_time = time.time()
        trace = observability.track_query(
            session_id=session_id,
            query=request.message,
            metadata={
                "message_count": len(session.messages) if session else 1,
                "session_created": session.created_at.isoformat() if session else None
            }
        )
        
        # Get response from Data Science Multi-Agent System
        from app.data_science.tools import ToolContext
        context = ToolContext()
        context.update_state("session_id", session_id)
        context.update_state("observability_trace", trace)  # Pass trace to agents
        
        # Get fresh session data including the new user message
        fresh_session = session_manager.get_session(session_id)
        if fresh_session:
            context.update_state("message_history", [msg.content for msg in fresh_session.messages[-5:]])
        
        # Get memory from persistent session manager
        memory = session_manager.get_session_memory(session_id)
        if memory:
            # Transfer memory state to ToolContext
            for key, value in memory.state.items():
                context.update_state(key, value)
            context.history = memory.history
        
        ai_response = await data_science_agent.process_message(request.message, context)
        
        # Calculate metrics
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        # Extract agent metrics from context
        agent_metrics = {
            "duration_ms": duration_ms,
            "agents_used": context.get_state("agents_called", []),
            "token_usage": context.get_state("total_tokens", 0),
            "sql_queries": context.get_state("sql_queries_executed", 0),
            "charts_generated": context.get_state("charts_generated", 0)
        }
        
        # Track response
        observability.track_response(trace, ai_response, agent_metrics)
        
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
        print(f"=== CHAT ERROR ===")
        print(f"Error in send_message: {e}")
        import traceback
        traceback.print_exc()
        logger.error(f"Error in send_message: {e}")
        # Track error if we have a trace
        if 'trace' in locals() and trace:
            observability.track_error(trace, str(e), type(e).__name__)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str, http_request: Request):
    """Get chat history for a session"""
    try:
        # Get authenticated user
        user_id = get_user_id(http_request)
        
        # Verify session belongs to user
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if hasattr(session, 'user_id') and session.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied to this session")
        
        messages = session_manager.get_messages(session_id)
        return ChatHistoryResponse(
            messages=messages,
            session_id=session_id
        )
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/chat/session/{session_id}")
async def delete_session(session_id: str, http_request: Request):
    """Delete a chat session"""
    try:
        # Get authenticated user
        user_id = get_user_id(http_request)
        
        # Verify session belongs to user
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if hasattr(session, 'user_id') and session.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied to this session")
        
        success = session_manager.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"message": "Session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/chat/session/{session_id}/title")
async def update_session_title(session_id: str, request: UpdateSessionTitleRequest, http_request: Request):
    """Update a session's title"""
    try:
        # Get authenticated user
        user_id = get_user_id(http_request)
        
        # Verify session belongs to user
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if hasattr(session, 'user_id') and session.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied to this session")
        
        success = session_manager.update_session_title(session_id, request.title)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"message": "Session title updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session title: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/sessions")
async def list_sessions(http_request: Request):
    """List chat sessions for the authenticated user"""
    try:
        # Get authenticated user
        user_id = get_user_id(http_request)
        
        # List only sessions for this user
        sessions = db_manager.list_sessions(user_id=user_id)
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