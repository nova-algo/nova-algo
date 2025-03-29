from typing import Dict, List, Any, Optional
import logging
import uuid

from ..websockets.websocket_manager import WebSocketManager, websocket_manager as connection_manager
from ..intelligence.agent_kit.agent_manager import AgentManager
from ..database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class ChatService:
    """
    Service layer for non-WebSocket chat operations.
    Primarily handles REST API endpoints and administrative functions.
    Real-time chat happens through WebSocket handlers.
    """
    
    def __init__(self, 
                 db_manager: DatabaseManager,
                 agent_manager: AgentManager,
                 websocket_manager: Optional[WebSocketManager] = None):
        self.db_manager = db_manager
        self.agent_manager = agent_manager
        self.websocket_manager = websocket_manager

    async def get_single_response(self, 
                                user_id: str, 
                                message: str, 
                                conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a single response through REST API (non-streaming)
        Used for simple queries that don't require real-time interaction
        """
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        try:
            # Use agent_manager to process the message
            response = await self.agent_manager.get_completion(
                user_id=user_id,
                message=message,
                conversation_id=conversation_id
            )
            
            return {
                "conversation_id": conversation_id,
                "response": response,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error getting single response: {str(e)}")
            return {
                "conversation_id": conversation_id,
                "response": f"Error: {str(e)}",
                "status": "error"
            }

    async def get_conversation_history(self, 
                                     user_id: str, 
                                     conversation_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history for a specific conversation
        Used by REST API endpoints
        """
        return await self.agent_manager.get_conversation_history(
            user_id=user_id,
            conversation_id=conversation_id
        )

    async def get_user_conversations(self, 
                                   user_id: str, 
                                   limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get list of user's conversations
        Used for conversation management UI
        """
        return await self.agent_manager.get_user_conversations(
            user_id=user_id,
            limit=limit
        )

    async def delete_conversation(self, 
                                user_id: str, 
                                conversation_id: str) -> Dict[str, Any]:
        """
        Delete a specific conversation
        Administrative function
        """
        try:
            await self.agent_manager.delete_conversation(
                user_id=user_id,
                conversation_id=conversation_id
            )
            return {"status": "success", "message": "Conversation deleted"}
        except Exception as e:
            logger.error(f"Error deleting conversation: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def clear_user_history(self, user_id: str) -> Dict[str, Any]:
        """
        Clear all conversation history for a user
        Administrative function
        """
        try:
            await self.agent_manager.clear_user_history(user_id)
            return {"status": "success", "message": "User history cleared"}
        except Exception as e:
            logger.error(f"Error clearing user history: {str(e)}")
            return {"status": "error", "message": str(e)}


# from typing import Dict, Any, List
# import logging
# import asyncio

# from rebalancr.database.db_manager import DatabaseManager
# from rebalancr.intelligence.agent_kit.chat_agent import PortfolioAgent
# from rebalancr.intelligence.allora.client import AlloraClient
# from rebalancr.strategy.engine import StrategyEngine

# logger = logging.getLogger(__name__)

# class ChatService:
#     """
#     Orchestrates the interaction between user chat, AgentKit, and Allora
    
#     Following Rose Heart's advice:
#     - AgentKit handles user intent and blockchain operations
#     - Allora provides market sentiment/predictions
#     - Strategy engine uses statistical methods for calculations
#     """
    
#     def __init__(self, 
#                  db_manager: DatabaseManager,
#                  portfolio_agent: PortfolioAgent,
#                  allora_client: AlloraClient,
#                  strategy_engine: StrategyEngine):
#         self.db_manager = db_manager
#         self.portfolio_agent = portfolio_agent
#         self.allora_client = allora_client
#         self.strategy_engine = strategy_engine
        
#     async def process_message(self, user_id: str, message: str, conversation_id: str = None):
#         """
#         Process a user message through the entire pipeline
        
#         1. Store message in chat history
#         2. Process with AgentKit to understand intent
#         3. If market-related, fetch Allora predictions
#         4. If action-required, use strategy engine for calculations
#         5. Execute through AgentKit
#         """
#         # Store incoming message
#         stored_message = await self._store_message(user_id, message, "user", conversation_id)
#         conversation_id = stored_message.get("conversation_id")
        
#         # Start response streaming from the agent
#         response_stream = self.portfolio_agent.process_message(user_id, message, conversation_id)
        
#         # Process agent responses with additional context if needed
#         complete_response = ""
#         async for chunk in response_stream:
#             response_type = chunk.get("type")
#             content = chunk.get("content", "")
            
#             # Enrich with Allora data if relevant
#             if self._is_market_related(content):
#                 allora_context = await self._get_allora_predictions(content)
#                 if allora_context:
#                     # Store system message with Allora insights
#                     await self._store_message(
#                         user_id, 
#                         f"Market insight: {allora_context}", 
#                         "system", 
#                         conversation_id
#                     )
            
#             # If action required, use statistical engine following Rose Heart's advice
#             if response_type == "tool_execution" and self._needs_rebalancing_calculation(content):
#                 # Use statistical methods from strategy engine, not AI
#                 allocation_data = await self.strategy_engine.calculate_optimal_allocation(user_id)
#                 # Enrich response with statistical analysis
#                 content += f"\n\nStatistical analysis suggests: {allocation_data}"
            
#             # Store agent's response chunk
#             await self._store_message(user_id, content, response_type, conversation_id)
            
#             # Accumulate complete response
#             complete_response += content + "\n"
            
#             # Return the chunk to allow streaming to user
#             yield chunk
        
#         # Return final response
#         return complete_response
    
#     async def _store_message(self, user_id, message, message_type, conversation_id=None):
#         """Store message in chat history database"""
#         message_data = {
#             "user_id": user_id,
#             "message": message,
#             "message_type": message_type,
#             "conversation_id": conversation_id
#         }
        
#         return await self.db_manager.insert_chat_message(message_data)
        
#     def _is_market_related(self, message):
#         """Check if message is market related and needs Allora predictions"""
#         market_keywords = ["price", "market", "trend", "prediction", "sentiment"]
#         return any(keyword in message.lower() for keyword in market_keywords)
        
#     async def _get_allora_predictions(self, message):
#         """Get relevant Allora predictions based on message content"""
#         # Extract assets mentioned in message
#         assets = self._extract_assets(message)
        
#         if not assets:
#             return None
            
#         results = {}
#         for asset in assets:
#             if asset in ["ETH", "BTC", "SOL", "BNB", "ARB"]:
#                 # Get predictions for supported assets
#                 predictions = {}
                
#                 # Get short-term prediction
#                 try:
#                     short_term = await self.allora_client.get_topic_prediction(f"{asset}_5min")
#                     predictions["short_term"] = short_term
#                 except:
#                     pass
                    
#                 # Get medium-term prediction
#                 try:
#                     medium_term = await self.allora_client.get_topic_prediction(f"{asset}_10min") 
#                     predictions["medium_term"] = medium_term
#                 except:
#                     pass
                    
#                 # Get long-term prediction
#                 try:
#                     long_term = await self.allora_client.get_topic_prediction(f"{asset}_24h")
#                     predictions["long_term"] = long_term
#                 except:
#                     pass
                    
#                 results[asset] = predictions
                
#         # Format results as human-readable text
#         if results:
#             return self._format_predictions(results)
#         return None
    
#     def _extract_assets(self, message):
#         """Extract mentioned assets from message"""
#         assets = []
#         if "eth" in message.lower() or "ethereum" in message.lower():
#             assets.append("ETH")
#         if "btc" in message.lower() or "bitcoin" in message.lower():
#             assets.append("BTC")
#         if "sol" in message.lower() or "solana" in message.lower():
#             assets.append("SOL")
#         if "bnb" in message.lower() or "binance" in message.lower():
#             assets.append("BNB")
#         if "arb" in message.lower() or "arbitrum" in message.lower():
#             assets.append("ARB")
#         return assets
        
#     def _format_predictions(self, predictions):
#         """Format predictions as human-readable text"""
#         result = ""
#         for asset, timeframes in predictions.items():
#             result += f"{asset} predictions:\n"
            
#             for timeframe, prediction in timeframes.items():
#                 direction = "up" if prediction.get("value", 0) > 0 else "down"
#                 confidence = round(prediction.get("confidence", 0) * 100)
#                 result += f"  • {timeframe}: {direction} with {confidence}% confidence\n"
                
#         return result
        
#     def _needs_rebalancing_calculation(self, content):
#         """Check if content requires rebalancing calculation"""
#         rebalance_keywords = ["rebalance", "portfolio", "allocation", "optimize", "adjust"]
#         return any(keyword in content.lower() for keyword in rebalance_keywords)
        
#     async def _get_rebalance_analysis(self, user_id, portfolio_id):
#         # Call the full analysis method in strategy engine
#         analysis = await self.strategy_engine.analyze_rebalance_opportunity(user_id, portfolio_id)
#         return analysis 