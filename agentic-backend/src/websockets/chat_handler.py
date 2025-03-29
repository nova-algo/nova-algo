# import json
# import logging
# import asyncio
# from typing import Dict, Any

# from ..intelligence.agent_kit.chat_agent import PortfolioAgent
# from ..chat.history_manager import ChatHistoryManager
# from ..websockets.websocket_manager import websocket_manager as connection_manager

# logger = logging.getLogger(__name__)

# class ChatWebSocketHandler:
#     """
#     WebSocket handler for chat interactions with the agent
    
#     Manages bidirectional communication between frontend and agent
#     """
    
#     def __init__(self, 
#                  portfolio_agent: PortfolioAgent,
#                  chat_history_manager: ChatHistoryManager):
#         self.portfolio_agent = portfolio_agent
#         self.chat_history_manager = chat_history_manager
        
#     async def handle_message(self, websocket, user_id: str, data: Dict[str, Any]):
#         """Handle incoming WebSocket messages"""
#         try:
#             message_type = data.get("type")
            
#             if message_type == "chat_message":
#                 await self._handle_chat_message(websocket, user_id, data)
#             elif message_type == "load_history":
#                 await self._handle_load_history(websocket, user_id, data)
#             else:
#                 logger.warning(f"Unknown message type: {message_type}")
                
#         except Exception as e:
#             logger.error(f"Error handling websocket message: {str(e)}")
#             await connection_manager.send_personal_message(
#                 {
#                     "type": "error",
#                     "message": f"Error: {str(e)}"
#                 },
#                 user_id
#             )
    
#     async def _handle_chat_message(self, websocket, user_id: str, data: Dict[str, Any]):
#         """Process chat message and route to agent"""
#         message = data.get("message", "")
#         conversation_id = data.get("conversation_id")
        
#         if not message:
#             return
            
#         # Store user message in history
#         stored_message = await self.chat_history_manager.store_message(
#             user_id=user_id,
#             message=message,
#             message_type="user",
#             conversation_id=conversation_id
#         )
        
#         # Make sure we have a conversation_id
#         conversation_id = stored_message["conversation_id"]
        
#         # Send acknowledgment to user
#         await connection_manager.send_personal_message(
#             {
#                 "type": "message_received",
#                 "message_id": stored_message["id"],
#                 "conversation_id": conversation_id
#             },
#             user_id
#         )
        
#         # Process with agent and stream responses
#         async for response in self.portfolio_agent.process_message(
#             user_id=user_id,
#             message=message,
#             conversation_id=conversation_id
#         ):
#             # Store agent response in history
#             stored_response = await self.chat_history_manager.store_message(
#                 user_id=user_id,
#                 message=response["content"],
#                 message_type=response["type"],
#                 conversation_id=conversation_id
#             )
            
#             # Send to WebSocket
#             await connection_manager.send_personal_message(
#                 {
#                     "type": response["type"],
#                     "message": response["content"],
#                     "message_id": stored_response["id"],
#                     "conversation_id": conversation_id
#                 },
#                 user_id
#             )
            
#             # If this is a tool execution (action), also notify about the operation
#             if response["type"] == "tool_execution":
#                 await connection_manager.send_personal_message(
#                     {
#                         "type": "action_execution",
#                         "action": self._extract_action_type(response["content"]),
#                         "status": "in_progress",
#                         "conversation_id": conversation_id
#                     },
#                     user_id
#                 )
    
#     async def _handle_load_history(self, websocket, user_id: str, data: Dict[str, Any]):
#         """Load and send conversation history"""
#         conversation_id = data.get("conversation_id")
#         limit = data.get("limit", 50)  # Default to 50 messages
        
#         if not conversation_id:
#             # Get list of conversations with limit
#             conversations = await self.chat_history_manager.get_user_conversations(user_id, limit)
#             await connection_manager.send_personal_message(
#                 {
#                     "type": "conversation_list",
#                     "conversations": conversations
#                 },
#                 user_id
#             )
#         else:
#             # Add error handling for invalid conversation_id
#             # Get specific conversation history with limit
#             messages = await self.chat_history_manager.get_conversation(conversation_id, limit)
#             await connection_manager.send_personal_message(
#                 {
#                     "type": "conversation_history",
#                     "conversation_id": conversation_id,
#                     "messages": messages
#                 },
#                 user_id
#             )
    
#     def _extract_action_type(self, content: str) -> str:
#         """Extract action type from tool execution content"""
#         if "deposit" in content.lower():
#             return "deposit"
#         elif "withdraw" in content.lower():
#             return "withdraw"
#         elif "transfer" in content.lower():
#             return "transfer"
#         elif "trade" in content.lower() or "swap" in content.lower():
#             return "trade"
#         else:
#             return "blockchain_operation"



# # import json
# # import asyncio
# # import logging
# # from typing import Dict, Any, Optional

# # from ..intelligence.strategy_engine import StrategyEngine
# # from ..intelligence.allora.client import AlloraClient
# # from ..intelligence.market_analysis import MarketAnalyzer
# # from ..intelligence.agent_kit.client import AgentKitClient
# # from ..intelligence.market_data import MarketDataService
# # from ..api.websocket import connection_manager

# # logger = logging.getLogger(__name__)

# # class ChatWebSocketHandler:
# #     """
# #     Handles WebSocket connections for chat and portfolio analysis,
# #     integrating with the intelligence layer
# #     """
    
# #     def __init__(
# #         self, 
# #         strategy_engine: StrategyEngine,
# #         agent_kit_client: AgentKitClient
# #     ):
# #         self.strategy_engine = strategy_engine
# #         self.agent_kit_client = agent_kit_client
        
# #     async def handle_message(self, websocket, user_id: str, data: Dict[str, Any]):
# #         """Process incoming WebSocket messages"""
# #         try:
# #             message_type = data.get("type", "")
            
# #             if message_type == "chat_message":
# #                 await self.handle_chat_message(websocket, user_id, data)
# #             elif message_type == "analyze_portfolio":
# #                 await self.handle_analyze_portfolio(websocket, user_id, data)
# #             elif message_type == "rebalance_portfolio":
# #                 await self.handle_rebalance_portfolio(websocket, user_id, data)
# #             elif message_type == "get_sentiment":
# #                 await self.handle_get_sentiment(websocket, user_id, data)
# #             else:
# #                 # Echo back for testing
# #                 await connection_manager.send_personal_message(
# #                     {"type": "echo", "data": data},
# #                     user_id
# #                 )
# #         except Exception as e:
# #             logger.error(f"Error handling message: {str(e)}")
# #             await connection_manager.send_personal_message(
# #                 {
# #                     "type": "error",
# #                     "message": f"Error processing request: {str(e)}"
# #                 },
# #                 user_id
# #             )
    
# #     async def handle_chat_message(self, websocket, user_id: str, data: Dict[str, Any]):
# #         """Process chat messages from user"""
# #         message = data.get("message", "")
        
# #         # Send message to AgentKit for processing
# #         response = await self.agent_kit_client.send_message(user_id, message)
        
# #         # Send response back to user
# #         await connection_manager.send_personal_message(
# #             {
# #                 "type": "chat_response",
# #                 "content": response.content,
# #                 "timestamp": response.timestamp
# #             },
# #             user_id
# #         )
    
# #     async def handle_analyze_portfolio(self, websocket, user_id: str, data: Dict[str, Any]):
# #         """Analyze portfolio using dual approach (AI + statistics)"""
# #         portfolio_id = data.get("portfolio_id")
        
# #         # Send processing update
# #         await connection_manager.send_personal_message(
# #             {
# #                 "type": "processing_update",
# #                 "status": "analyzing",
# #                 "message": "Analyzing portfolio using AI and statistical methods..."
# #             },
# #             user_id
# #         )
        
# #         # Use Strategy Engine to analyze portfolio
# #         # This implements Rose Heart's dual approach
# #         result = await self.strategy_engine.analyze_portfolio(user_id, portfolio_id)
        
# #         # Send results back to user
# #         await connection_manager.send_personal_message(
# #             {
# #                 "type": "analysis_result",
# #                 "status": "complete",
# #                 "result": result
# #             },
# #             user_id
# #         )
    
# #     async def handle_rebalance_portfolio(self, websocket, user_id: str, data: Dict[str, Any]):
# #         """Execute portfolio rebalancing"""
# #         portfolio_id = data.get("portfolio_id")
        
# #         # Send processing update
# #         await connection_manager.send_personal_message(
# #             {
# #                 "type": "processing_update",
# #                 "status": "rebalancing",
# #                 "message": "Executing portfolio rebalance..."
# #             },
# #             user_id
# #         )
        
# #         # Here you would implement the actual rebalancing logic
# #         # For now, just return a dummy response
        
# #         await connection_manager.send_personal_message(
# #             {
# #                 "type": "rebalance_result",
# #                 "status": "complete",
# #                 "result": {
# #                     "portfolio_id": portfolio_id,
# #                     "success": True,
# #                     "message": "Portfolio rebalanced successfully",
# #                     "transactions": [
# #                         {"asset": "BTC", "action": "buy", "amount": 0.1},
# #                         {"asset": "ETH", "action": "sell", "amount": 1.5}
# #                     ]
# #                 }
# #             },
# #             user_id
# #         )
    
# #     async def handle_get_sentiment(self, websocket, user_id: str, data: Dict[str, Any]):
# #         """Get sentiment analysis for an asset (AI-only approach)"""
# #         asset = data.get("asset")
        
# #         if not asset:
# #             await connection_manager.send_personal_message(
# #                 {
# #                     "type": "error",
# #                     "message": "Asset symbol is required"
# #                 },
# #                 user_id
# #             )
# #             return
        
# #         # Following Rose Heart's advice: Use AI only for sentiment analysis
# #         sentiment = await self.strategy_engine.allora_client.analyze_sentiment(
# #             asset,
# #             await self.strategy_engine.market_data_service.get_social_content(asset)
# #         )
        
# #         await connection_manager.send_personal_message(
# #             {
# #                 "type": "sentiment_result",
# #                 "asset": asset,
# #                 "sentiment": sentiment
# #             },
# #             user_id
# #         ) 