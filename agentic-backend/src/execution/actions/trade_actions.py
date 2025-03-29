# from typing import Dict, Any, List, Optional
# from .base_action import BaseAction, ActionParameter

# class TradeAction(BaseAction):
#     """Action to buy or sell a specific asset"""
    
#     def __init__(self, trade_agent):
#         self.trade_agent = trade_agent
    
#     def get_name(self) -> str:
#         return "execute_trade"
    
#     def get_description(self) -> str:
#         return "Buy or sell a specific amount of cryptocurrency"
    
#     def get_parameters(self) -> List[ActionParameter]:
#         return [
#             {"name": "asset", "type": "string", "description": "Symbol of the asset to trade (e.g., ETH, USDC)", "required": True},
#             {"name": "amount", "type": "number", "description": "Amount to trade", "required": True},
#             {"name": "action", "type": "string", "description": "Either 'buy' or 'sell'", "required": True}
#         ]
    
#     async def execute(self, user_id: str, asset: str, amount: float, action: str) -> Dict[str, Any]:
#         # Validate parameters
#         if action.lower() not in ["buy", "sell"]:
#             return {"success": False, "message": "Action must be 'buy' or 'sell'"}
        
#         if amount <= 0:
#             return {"success": False, "message": "Amount must be greater than 0"}
        
#         # Execute the trade
#         return await self.trade_agent.execute_trade(
#             user_id=user_id,
#             asset=asset,
#             amount=amount,
#             action=action.lower()
#         )

# class RebalanceAction(BaseAction):
#     """Action to rebalance a portfolio to target allocations"""
    
#     def __init__(self, trade_agent, strategy_engine):
#         self.trade_agent = trade_agent
#         self.strategy_engine = strategy_engine
    
#     def get_name(self) -> str:
#         return "rebalance_portfolio"
    
#     def get_description(self) -> str:
#         return "Rebalance your portfolio to align with a target allocation or strategy"
    
#     def get_parameters(self) -> List[ActionParameter]:
#         return [
#             {"name": "strategy", "type": "string", "description": "Strategy profile (e.g., 'conservative', 'balanced', 'aggressive')", "required": False}
#         ]
    
#     async def execute(self, user_id: str, strategy: Optional[str] = "balanced") -> Dict[str, Any]:
#         # Get target allocation from strategy
#         target_allocation = await self.strategy_engine.get_recommended_allocation(strategy)
        
#         # Execute rebalance
#         return await self.trade_agent.rebalance_portfolio(
#             user_id=user_id,
#             target_weights=target_allocation
#         ) 