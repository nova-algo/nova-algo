from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from ..dependencies import get_chat_service
from .auth import get_current_user_id
from ...services.chat_service import ChatService
from ...intelligence.agent_kit.agent_manager import AgentManager
from ...config import Settings, get_settings

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)

class MessageRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class MessageResponse(BaseModel):
    conversation_id: str
    message_received: bool

@router.post("/message", response_model=MessageResponse)
async def send_message(
    request: MessageRequest,
    user_id: str = Depends(get_current_user_id),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Send a message to the chat agent"""
    agent_manager = AgentManager.get_instance(get_settings())
    response = await agent_manager.get_agent_response(user_id, request.message, request.conversation_id)
    return response

@router.get("/conversations")
async def get_conversations(
    limit: int = 10,
    user_id: str = Depends(get_current_user_id)
):
    """Get list of user's conversations"""
    agent_manager = AgentManager.get_instance(get_settings())
    conversations = await agent_manager.history_manager.get_user_conversations(user_id, limit)
    return {"conversations": conversations}

@router.get("/conversation/{conversation_id}")
async def get_conversation_history(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get message history for a specific conversation"""
    messages = await chat_service.get_conversation_history(user_id, conversation_id)
    return {"messages": messages} 