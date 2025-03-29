import logging
from typing import Dict, List, Any
from datetime import datetime
import uuid

from ..database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class ChatHistoryManager:
    """Manages persistent storage and retrieval of chat histories"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        
    async def add_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store a chat message in the database
        
        Args:
            message_data: Dictionary with message details
                - user_id: User identifier
                - message: Message content
                - message_type: Type of message (user, agent, system)
                - conversation_id: Optional conversation ID
                - timestamp: Optional timestamp
        
        Returns:
            Dictionary with inserted message details including ID
        """
        return await self.db_manager.insert_chat_message(message_data)
        
    async def store_message(self, 
                      user_id: str, 
                      message: str, 
                      message_type: str, 
                      conversation_id: str = None) -> Dict[str, Any]:
        """
        Store a chat message in the database
        
        Args:
            user_id: User identifier
            message: Message content
            message_type: Type of message (user, agent, system)
            conversation_id: Optional conversation ID (creates new if None)
        """
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            
        # Create message record
        message_data = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "message": message,
            "message_type": message_type,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in database using add_message
        return await self.add_message(message_data)
        
    async def get_messages(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve messages for a specific conversation
        
        Args:
            conversation_id: Conversation identifier
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries
        """
        return await self.db_manager.get_chat_messages(conversation_id, limit)
        
    async def get_conversation(self, 
                         conversation_id: str, 
                         limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve conversation history from database"""
        return await self.get_messages(conversation_id, limit)
        
    async def get_user_conversations(self, 
                               user_id: str, 
                               limit: int = 10) -> List[Dict[str, Any]]:
        """Get list of user's conversations"""
        return await self.db_manager.get_user_conversations(user_id, limit) 