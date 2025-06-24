from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"

class Message(BaseModel):
    id: str
    content: str
    role: MessageRole
    timestamp: datetime
    session_id: str

class ChatSession(BaseModel):
    id: str
    title: str
    messages: List[Message]
    created_at: datetime
    updated_at: datetime

class SendMessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class SendMessageResponse(BaseModel):
    message: str
    session_id: str
    message_id: str

class ChatHistoryResponse(BaseModel):
    messages: List[Message]
    session_id: str

class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    size: int
    status: str
    message: str