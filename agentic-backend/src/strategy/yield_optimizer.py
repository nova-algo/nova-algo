import logging
from typing import Dict, List, Any
import random

logger = logging.getLogger(__name__)

class YieldOptimizer:
    """
    Identifies and optimizes yield opportunities across different protocols.
    
    Following Rose Heart's advice, this uses statistical methods for numerical
    calculations rather than AI.
    """
    
    def __init__(self, db_manager, market_data_service, config):
        self.db_manager = db_manager
        self.market_data_service = market_data_service
        self.config = config
        
    async def find_opportunities(self, portfolio_id: int) -> List[Dict[str, Any]]:
        """Find yield opportunities for portfolio assets"""
        try:
            # Get portfolio data
            portfolio = await self.db_manager.get_portfolio(portfolio_id)
            assets = portfolio.get("assets", [])
            
            # Get yield data for relevant assets and protocols
            yield_data = await self.market_data_service.get_yield_data(
                [asset["symbol"] for asset in assets]
            )
            
            opportunities = []
            
            for asset in assets:
                symbol = asset["symbol"]
                amount = asset["amount"]
                
                if symbol not in yield_data:
                    continue
                
                asset_yields = yield_data[symbol]
                
                # Find best yield opportunity
                best_opportunity = None
                best_apy = 0
                
                for protocol in asset_yields:
                    protocol_yield = asset_yields[protocol]
                    apy = protocol_yield.get("apy", 0)
                    
                    # Filter out opportunities below minimum APY
                    if apy < self.config.MIN_APY:
                        continue
                    
                    # Check protocol risk level - stick to statistical approach
                    risk_level = protocol_yield.get("risk_level", "high")
                    if risk_level == "high" and apy < self.config.MIN_HIGH_RISK_APY:
                        continue
                    
                    # Check liquidity - ensure we can exit the position
                    liquidity = protocol_yield.get("liquidity", 0)
                    if amount > liquidity * 0.1:  # Don't take more than 10% of liquidity
                        continue
                    
                    # Check if this is better than current best
                    if apy > best_apy:
                        best_apy = apy
                        best_opportunity = {
                            "symbol": symbol,
                            "protocol": protocol,
                            "apy": apy,
                            "risk_level": risk_level,
                            "liquidity": liquidity,
                            "available_amount": amount,
                            "estimated_yield": amount * apy / 100
                        }
                
                if best_opportunity:
                    opportunities.append(best_opportunity)
            
            # Sort opportunities by estimated yield
            opportunities.sort(key=lambda x: x["estimated_yield"], reverse=True)
            
            return opportunities
        except Exception as e:
            logger.error(f"Error finding yield opportunities: {str(e)}")
            return []
    
    async def optimize_yields(self, portfolio_id: int) -> Dict[str, Any]:
        """Optimize yield allocation across protocols"""
        try:
            # Get portfolio data
            portfolio = await self.db_manager.get_portfolio(portfolio_id)
            
            # Find opportunities
            opportunities = await self.find_opportunities(portfolio_id)
            
            # Calculate optimal allocation - follow Rose Heart's statistical approach
            allocations = await self._calculate_optimal_allocation(opportunities, portfolio)
            
            # Calculate expected returns
            total_investment = sum(allocation["amount"] for allocation in allocations)
            weighted_apy = sum(allocation["amount"] * allocation["apy"] / total_investment 
                              for allocation in allocations) if total_investment > 0 else 0
            
            annual_yield = total_investment * weighted_apy / 100
            
            return {
                "portfolio_id": portfolio_id,
                "allocations": allocations,
                "total_investment": total_investment,
                "weighted_apy": weighted_apy,
                "estimated_annual_yield": annual_yield
            }
        except Exception as e:
            logger.error(f"Error optimizing yields: {str(e)}")
            return {
                "portfolio_id": portfolio_id,
                "error": str(e),
                "allocations": []
            }
    
    async def _calculate_optimal_allocation(self, opportunities, portfolio):
        """Calculate optimal allocation across yield opportunities"""
        # Per Rose Heart's advice - use statistical optimization, not AI
        
        # Start with a risk-weighted approach
        risk_weights = {
            "low": 1.0,
            "medium": 0.7,
            "high": 0.4
        }
        
        # Calculate risk-adjusted APY
        for opportunity in opportunities:
            risk_level = opportunity.get("risk_level", "medium")
            risk_weight = risk_weights.get(risk_level, 0.5)
            opportunity["risk_adjusted_apy"] = opportunity["apy"] * risk_weight
        
        # Sort by risk-adjusted APY
        opportunities.sort(key=lambda x: x["risk_adjusted_apy"], reverse=True)
        
        # Allocate assets based on risk tolerance
        allocations = []
        remaining_amount = {}
        
        # Initialize remaining amounts
        for asset in portfolio.get("assets", []):
            remaining_amount[asset["symbol"]] = asset["amount"]
        
        # Allocate to opportunities
        for opportunity in opportunities:
            symbol = opportunity["symbol"]
            
            if symbol not in remaining_amount or remaining_amount[symbol] <= 0:
                continue
            
            # Calculate amount to allocate
            risk_level = opportunity.get("risk_level", "medium")
            allocation_percentage = {
                "low": 0.8,     # Allocate up to 80% of asset to low-risk
                "medium": 0.5,  # Allocate up to 50% of asset to medium-risk
                "high": 0.2     # Allocate up to 20% of asset to high-risk
            }.get(risk_level, 0.3)
            
            # Get original asset amount
            original_amount = next((asset["amount"] for asset in portfolio.get("assets", []) 
                                  if asset["symbol"] == symbol), 0)
            
            # Calculate amount to allocate
            amount_to_allocate = min(
                remaining_amount[symbol],
                original_amount * allocation_percentage
            )
            
            # Ensure the amount is not too small
            if amount_to_allocate > self.config.MIN_ALLOCATION_AMOUNT:
                # Create allocation
                allocations.append({
                    "symbol": symbol,
                    "protocol": opportunity["protocol"],
                    "amount": amount_to_allocate,
                    "apy": opportunity["apy"],
                    "risk_level": risk_level,
                    "estimated_yield": amount_to_allocate * opportunity["apy"] / 100
                })
                
                # Update remaining amount
                remaining_amount[symbol] -= amount_to_allocate
        
        return allocations
    
    async def execute_yield_strategy(self, portfolio_id: int) -> Dict[str, Any]:
        """Execute the optimal yield strategy"""
        try:
            # Get optimal allocations
            optimization = await self.optimize_yields(portfolio_id)
            
            # In a real implementation, this would call APIs to deposit into protocols
            # For now, simulate successful execution
            
            executed_allocations = []
            
            for allocation in optimization.get("allocations", []):
                # Simulate execution with slight amount adjustment
                executed_amount = allocation["amount"] * 0.995  # 0.5% slippage/fees
                
                executed_allocations.append({
                    "symbol": allocation["symbol"],
                    "protocol": allocation["protocol"],
                    "requested_amount": allocation["amount"],
                    "executed_amount": executed_amount,
                    "apy": allocation["apy"],
                    "transaction_id": f"tx_{random.randint(10000000, 99999999)}",
                    "status": "completed"
                })
            
            return {
                "portfolio_id": portfolio_id,
                "success": True,
                "allocations": executed_allocations,
                "total_allocated": sum(alloc["executed_amount"] for alloc in executed_allocations),
                "estimated_annual_yield": sum(alloc["executed_amount"] * alloc["apy"] / 100 
                                            for alloc in executed_allocations)
            }
        except Exception as e:
            logger.error(f"Error executing yield strategy: {str(e)}")
            return {
                "portfolio_id": portfolio_id,
                "success": False,
                "error": str(e)
            }
    
    async def withdraw_from_protocol(self, 
                               portfolio_id: int, 
                               symbol: str, 
                               protocol: str, 
                               amount: float) -> Dict[str, Any]:
        """Withdraw assets from a yield protocol"""
        try:
            # In a real implementation, this would call APIs to withdraw from protocols
            # For now, simulate successful withdrawal
            
            # Simulate some fees
            received_amount = amount * 0.997  # 0.3% withdrawal fee
            
            return {
                "portfolio_id": portfolio_id,
                "symbol": symbol,
                "protocol": protocol,
                "requested_amount": amount,
                "received_amount": received_amount,
                "transaction_id": f"tx_{random.randint(10000000, 99999999)}",
                "status": "completed",
                "timestamp": "2023-04-15T12:34:56Z"
            }
        except Exception as e:
            logger.error(f"Error withdrawing from protocol: {str(e)}")
            return {
                "portfolio_id": portfolio_id,
                "symbol": symbol,
                "protocol": protocol,
                "success": False,
                "error": str(e)
            }
