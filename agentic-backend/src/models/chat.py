from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime
import uuid

class Message(BaseModel):
    content: str
    is_user: bool
    timestamp: datetime = Field(default_factory=datetime.now)
    message_type: str = "chat_message"  # chat_message, tool_execution, action_result, error
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    
    @classmethod
    def from_websocket_data(cls, data: dict):
        """Convert WebSocket JSON to ChatRequest"""
        return cls(
            message=data.get("message", ""),
            conversation_id=data.get("conversation_id")
        )

class ChatResponse(BaseModel):
    content: str
    message_type: str
    conversation_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    
    @classmethod
    def from_agent_response(cls, response: dict, conversation_id: str):
        """Convert agent response to ChatResponse"""
        return cls(
            content=response.get("content", ""),
            message_type=response.get("type", "agent_message"),
            conversation_id=conversation_id,
        )
    
    def to_websocket_message(self):
        """Convert to WebSocket-friendly format"""
        return {
            "type": self.message_type,
            "content": self.content,
            "conversation_id": self.conversation_id,
            "timestamp": self.timestamp.isoformat()
        }

class ConversationSummary(BaseModel):
    id: str
    title: str  # Generated from first message or explicit title
    last_message_time: datetime
    message_count: int
    
class ChatHistory(BaseModel):
    messages: List[Message]
    user_id: str
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))




