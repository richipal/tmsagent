from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import logging
from app.core.session_manager import session_manager
from app.data_science.agent import root_agent as data_science_agent
from app.models.chat import MessageRole

logger = logging.getLogger(__name__)
router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected for session: {session_id}")
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected for session: {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_text(json.dumps(message))
    
    async def broadcast_typing(self, session_id: str, is_typing: bool):
        await self.send_message(session_id, {
            "type": "typing",
            "isTyping": is_typing
        })

manager = ConnectionManager()

@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    # Get session_id from query params or create new session
    session_id = websocket.query_params.get("session_id")
    
    if session_id:
        session = session_manager.get_session(session_id)
        if not session:
            session = session_manager.create_session()
            session_id = session.id
    else:
        session = session_manager.create_session()
        session_id = session.id
    
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "message":
                user_message = message_data.get("content", "")
                
                # Add user message to session
                session_manager.add_message(
                    session_id=session_id,
                    content=user_message,
                    role=MessageRole.USER
                )
                
                # Send typing indicator
                await manager.broadcast_typing(session_id, True)
                
                try:
                    # Get response from Data Science Multi-Agent System
                    websocket_context = {
                        "session_id": session_id,
                        "connection_type": "websocket"
                    }
                    ai_response = await data_science_agent.process_message(user_message, websocket_context)
                    
                    # Add AI message to session
                    session_manager.add_message(
                        session_id=session_id,
                        content=ai_response,
                        role=MessageRole.ASSISTANT
                    )
                    
                    # Send response to client
                    await manager.send_message(session_id, {
                        "type": "message",
                        "content": ai_response,
                        "role": "assistant"
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await manager.send_message(session_id, {
                        "type": "message",
                        "content": "I apologize, but I encountered an error. Please try again.",
                        "role": "assistant"
                    })
                
                finally:
                    # Stop typing indicator
                    await manager.broadcast_typing(session_id, False)
                    
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(session_id)