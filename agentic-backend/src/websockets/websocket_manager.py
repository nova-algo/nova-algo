from typing import Dict, List, Any, Optional, Set
from fastapi import WebSocket
import json
import logging


logger = logging.getLogger(__name__)

class WebSocketManager:
    """
    Unified WebSocket connection manager with topic subscription capability
    and improved error handling.
    """
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Store topic subscriptions by user_id
        self.topic_subscriptions: Dict[str, Set[str]] = {}
        logger.info("WebSocket Manager initialized")
        
    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a new WebSocket client"""
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
            self.topic_subscriptions[user_id] = set()
            
        self.active_connections[user_id].append(websocket)
        logger.info(f"Client connected: {user_id}")
    
    async def disconnect(self, websocket: WebSocket, user_id: str):
        """Disconnect a specific client connection"""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
                logger.info(f"Client connection removed: {user_id}")
                
            # Clean up if no more connections
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                if user_id in self.topic_subscriptions:
                    del self.topic_subscriptions[user_id]
                logger.info(f"Client fully disconnected: {user_id}")
    
    def subscribe_to_topics(self, user_id: str, topics: List[str]):
        """Subscribe a user to specified topics"""
        if user_id not in self.topic_subscriptions:
            self.topic_subscriptions[user_id] = set()
        
        self.topic_subscriptions[user_id].update(topics)
        logger.info(f"User {user_id} subscribed to topics: {topics}")
        return list(self.topic_subscriptions[user_id])
    
    def unsubscribe_from_topics(self, user_id: str, topics: List[str]):
        """Unsubscribe a user from specified topics"""
        if user_id in self.topic_subscriptions:
            self.topic_subscriptions[user_id].difference_update(topics)
            logger.info(f"User {user_id} unsubscribed from topics: {topics}")
        return list(self.topic_subscriptions[user_id])
                
    async def send_personal_message(self, message: Any, user_id: str):
        """Send message to all connections of a specific user"""
        if user_id not in self.active_connections:
            logger.warning(f"Attempted to send message to non-connected user: {user_id}")
            return
            
        failed_connections = []
        for connection in self.active_connections[user_id]:
            try:
                if isinstance(message, dict):
                    await connection.send_json(message)
                else:
                    await connection.send_text(str(message))
            except Exception as e:
                logger.error(f"Error sending message to {user_id}: {str(e)}")
                failed_connections.append(connection)
                
        # Clean up failed connections
        for failed in failed_connections:
            await self.disconnect(failed, user_id)
                
    async def broadcast(self, message: Any):
        """Broadcast message to all connected users"""
        # Prepare message based on type
        if isinstance(message, dict):
            json_message = json.dumps(message)
            is_json = True
        else:
            json_message = str(message)
            is_json = False
            
        # Track users with failed connections for cleanup
        users_to_cleanup = {}
        
        for user_id, connections in self.active_connections.items():
            failed_connections = []
            for connection in connections:
                try:
                    if is_json:
                        await connection.send_json(json_message)
                    else:
                        await connection.send_text(json_message)
                except Exception as e:
                    logger.error(f"Broadcast error to {user_id}: {str(e)}")
                    failed_connections.append(connection)
            
            # Track failed connections
            if failed_connections:
                users_to_cleanup[user_id] = failed_connections
        
        # Clean up failed connections
        for user_id, failed_list in users_to_cleanup.items():
            for failed in failed_list:
                await self.disconnect(failed, user_id)
    
    async def broadcast_to_topic(self, topic: str, message: Any):
        """Send message to all users subscribed to a topic"""
        message_with_topic = {
            "topic": topic,
            "type": "topic_update",
            "data": message
        }
        
        # Get all users subscribed to this topic
        subscribed_users = [
            user_id for user_id, topics in self.topic_subscriptions.items()
            if topic in topics and user_id in self.active_connections
        ]
        
        logger.info(f"Broadcasting to topic {topic}: {len(subscribed_users)} recipients")
        
        # Send to each subscribed user
        for user_id in subscribed_users:
            await self.send_personal_message(message_with_topic, user_id)

# Global websocket manager instance
websocket_manager = WebSocketManager()