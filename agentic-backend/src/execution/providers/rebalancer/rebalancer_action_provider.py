"""
RebalancerActionProvider

Provides actions for portfolio rebalancing, implementing the AgentKit action provider pattern.
"""
import asyncio
from datetime import datetime
import json
import logging
from typing import Dict, List, Any, Optional, Type, Union, cast, TYPE_CHECKING, Tuple
from pydantic import BaseModel, Field, root_validator, validator
from decimal import Decimal

from coinbase_agentkit.action_providers.action_decorator import create_action
from coinbase_agentkit.action_providers.action_provider import ActionProvider
from coinbase_agentkit.network import Network
from coinbase_agentkit.wallet_providers import EvmWalletProvider

# Use TYPE_CHECKING for circular import prevention
if TYPE_CHECKING:
    from rebalancr.intelligence.intelligence_engine import IntelligenceEngine
else:
    # For runtime, just use Any
    IntelligenceEngine = Any

from rebalancr.intelligence.reviewer import TradeReviewer
from rebalancr.strategy.engine import StrategyEngine
from rebalancr.performance.analyzer import PerformanceAnalyzer
from rebalancr.database.db_manager import DatabaseManager
from rebalancr.execution.providers.kuru.kuru_action_provider import KuruActionProvider

logger = logging.getLogger(__name__)

# Supported networks for the rebalancer
SUPPORTED_NETWORKS = [1, 56, 137, 42161, 10, 10143]  # Ethereum, BSC, Polygon, Arbitrum, Optimism

class AnalyzePortfolioParams(BaseModel):
    """Parameters for portfolio analysis"""
    portfolio_id: int
    user_id: str = "current_user"
    include_sentiment: bool = True
    include_manipulation_check: bool = True
    
class ExecuteRebalanceParams(BaseModel):
    """Parameters for executing a portfolio rebalance"""
    portfolio_id: int
    user_id: str = "current_user"
    dry_run: bool = False  # If True, analyze but don't execute
    max_slippage_percent: float = Field(ge=0.1, le=5.0, default=1.0)
    
    @validator('max_slippage_percent')
    def validate_slippage(cls, v):
        if v < 0.1 or v > 5.0:
            raise ValueError('Slippage must be between 0.1% and 5.0%')
        return v
        
class SimulateRebalanceParams(BaseModel):
    """Parameters for simulating a portfolio rebalance"""
    portfolio_id: int
    user_id: str = "current_user"
    target_allocations: Dict[str, float] = Field(default_factory=dict)
    
    @root_validator(skip_on_failure=True)
    def validate_allocations(cls, values):
        allocations = values.get('target_allocations', {})
        if not allocations:
            raise ValueError('Target allocations must be provided')
            
        total = sum(allocations.values())
        if abs(total - 1.0) > 0.01:  # Allow small rounding errors
            raise ValueError(f'Target allocations must sum to 1.0 (got {total})')
            
        return values

class GetPerformanceParams(BaseModel):
    """Parameters for getting performance metrics"""
    portfolio_id: Optional[int] = None
    days: int = Field(ge=1, le=365, default=30)
    include_recommendations: bool = True
    
    @validator('days')
    def validate_days(cls, v):
        if v < 1 or v > 365:
            raise ValueError('Days must be between 1 and 365')
        return v

class EnableAutoRebalanceParams(BaseModel):
    """Parameters for enabling automatic rebalancing"""
    portfolio_name: str = "main"
    frequency: str = "daily"  # hourly, daily, weekly, monthly
    max_slippage: float = Field(ge=0.1, le=5.0, default=1.0)
    
    @validator('max_slippage')
    def validate_slippage(cls, v):
        if v < 0.1 or v > 5.0:
            raise ValueError('Slippage must be between 0.1% and 5.0%')
        return v
        
class DisableAutoRebalanceParams(BaseModel):
    """Parameters for disabling automatic rebalancing"""
    portfolio_name: str = "main"
    
class GetRebalancingStatusParams(BaseModel):
    """Parameters for getting rebalancing status"""
    portfolio_name: str = "main"

class RebalancerActionProvider(ActionProvider[EvmWalletProvider]):
    """
    Action provider for portfolio rebalancing
    
    Implements Rose Heart's dual-system approach:
    - AI for sentiment analysis (via Intelligence Engine)
    - Statistical methods for numerical operations (via Strategy Engine)
    - Additional validation layer (Trade Reviewer)
    """
    
    def __init__(
        self,
        wallet_provider: EvmWalletProvider,
        intelligence_engine: IntelligenceEngine = None,
        strategy_engine: StrategyEngine = None,
        trade_reviewer: TradeReviewer = None,
        performance_analyzer: PerformanceAnalyzer = None,
        db_manager: DatabaseManager = None,
        kuru_provider: KuruActionProvider = None,
        context: Dict[str, Any] = None,
        config: Dict[str, Any] = None
    ):
        super().__init__("rebalancer", [])
        self.wallet_provider = wallet_provider
        self.intelligence_engine = intelligence_engine
        self.strategy_engine = strategy_engine
        self.trade_reviewer = trade_reviewer
        self.performance_analyzer = performance_analyzer
        self.db_manager = db_manager
        self.kuru_provider = kuru_provider
        self.context = context or {"user_id": "current_user"}
        self.config = config
        
    def supports_network(self, network: Network) -> bool:
        """Check if the network is supported by this provider"""
        return network.protocol_family == "evm" and network.network_id in SUPPORTED_NETWORKS
    
    @create_action(
        name="analyze-portfolio",
        description="Analyze a portfolio and provide rebalancing recommendations",
        schema=AnalyzePortfolioParams
    )
    def analyze_portfolio(self, wallet_provider: EvmWalletProvider, args: Dict[str, Any]) -> str:
        """
        Analyze a portfolio and provide recommendations
        
        This uses the intelligence engine which combines:
        - Allora sentiment analysis (emotional signals)
        - Statistical methods (numerical signals)
        """
        params = AnalyzePortfolioParams(**args)
        
        try:
            intelligence_results = asyncio.run(self.intelligence_engine.analyze_portfolio(
                params.user_id, 
                params.portfolio_id
            ))
            
            # Additional strategy-specific analysis
            strategy_results = asyncio.run(self.strategy_engine.analyze_portfolio(
                intelligence_results.get("assets", [])
            ))
            
            # Get market conditions
            market_condition = strategy_results.get("market_condition", "normal")
            
            # Validate using the reviewer
            validation = None
            if params.include_sentiment and len(intelligence_results.get("assets", [])) > 0:
                validation = asyncio.run(self.trade_reviewer.validate_rebalance_plan(
                    intelligence_results.get("assets", []),
                    market_condition
                ))
            
            result = {
                "portfolio_id": params.portfolio_id,
                "rebalance_needed": intelligence_results.get("rebalance_needed", False),
                "assets": intelligence_results.get("assets", []),
                "cost_analysis": intelligence_results.get("cost_analysis", {}),
                "strategy_analysis": {
                    "market_condition": market_condition,
                    "risk_level": strategy_results.get("risk_level", "medium"),
                    "recommendations": strategy_results.get("recommendations", [])
                }
            }
            
            if validation:
                result["validation"] = {
                    "approved": validation.get("approved", False),
                    "approval_rate": validation.get("approval_rate", 0),
                    "overall_risk": validation.get("overall_risk", 5)
                }
                
            # Convert to string response like Kuru does
            return f"Portfolio Analysis Complete for ID {params.portfolio_id}. " + \
                  f"Rebalance needed: {result['rebalance_needed']}. " + \
                  f"Market condition: {market_condition}. " + \
                  f"Full details: {json.dumps(result, indent=2)}"
            
        except Exception as e:
            logger.error(f"Error analyzing portfolio: {str(e)}")
            return f"Error analyzing portfolio: {str(e)}"
    
    @create_action(
        name="execute-rebalance",
        description="Execute a portfolio rebalance based on AI and statistical analysis",
        schema=ExecuteRebalanceParams
    )
    def execute_rebalance(self, wallet_provider: EvmWalletProvider, args: Dict[str, Any]) -> str:
        """
        Execute a portfolio rebalance
        
        This implements Rose Heart's approach by:
        1. Getting recommendations from intelligence engine (AI + statistical)
        2. Validating with reviewer (3rd component)
        3. Only executing if all components agree
        4. Being cautious about fees (cost-benefit analysis)
        """
        params = ExecuteRebalanceParams(**args)
        
        try:
            # First, analyze the portfolio to get recommendations
            analysis_result_str = self.analyze_portfolio(wallet_provider, {
                "portfolio_id": params.portfolio_id,
                "user_id": params.user_id,
                "include_sentiment": True,
                "include_manipulation_check": True
            })
            
            # Parse the json from the string response
            import re
            json_match = re.search(r'Full details: ({.*})', analysis_result_str, re.DOTALL)
            if not json_match:
                return f"Failed to parse analysis results: {analysis_result_str}"
                
            analysis_result = json.loads(json_match.group(1))
                
            # Check if rebalancing is needed
            if not analysis_result.get("rebalance_needed", False):
                return f"Rebalancing not needed for portfolio {params.portfolio_id}. Analysis: {json.dumps(analysis_result, indent=2)}"
                
            # Check validation if available
            validation = analysis_result.get("validation", {})
            if not validation.get("approved", False) and validation:
                return f"Rebalancing not approved by validator. Approval rate: {validation.get('approval_rate', 0)}%. Analysis: {json.dumps(analysis_result, indent=2)}"
                
            # Check if dry run - if so, return the analysis without executing
            if params.dry_run:
                return f"Dry run requested. No trades executed. Analysis: {json.dumps(analysis_result, indent=2)}"
                
            # Execute the rebalance trades
            trades = analysis_result.get("cost_analysis", {}).get("trades", [])
            execution_results = []
            
            for trade in trades:
                symbol = trade.get("symbol")
                amount = trade.get("amount")
                value = trade.get("value")
                
                if amount > 0:
                    # Buy operation
                    execution_result = asyncio.run(self._execute_buy(
                        params.user_id,
                        symbol,
                        abs(amount),
                        params.max_slippage_percent
                    ))
                elif amount < 0:
                    # Sell operation
                    execution_result = asyncio.run(self._execute_sell(
                        params.user_id,
                        symbol,
                        abs(amount),
                        params.max_slippage_percent
                    ))
                else:
                    # Skip zero amount trades
                    continue
                    
                execution_results.append({
                    "symbol": symbol,
                    "amount": amount,
                    "value": value,
                    "success": execution_result.get("success", False),
                    "tx_hash": execution_result.get("tx_hash"),
                    "error": execution_result.get("error")
                })
                
            # Log the rebalance for performance tracking
            if execution_results:
                asyncio.run(self.performance_analyzer.log_rebalance({
                    "portfolio_id": params.portfolio_id,
                    "assets": analysis_result.get("assets", []),
                    "market_condition": analysis_result.get("strategy_analysis", {}).get("market_condition", "normal"),
                    "timestamp": analysis_result.get("timestamp")
                }))
                
            # Return the results
            all_succeeded = all(result.get("success", False) for result in execution_results)
            result_summary = {
                "portfolio_id": params.portfolio_id,
                "executed": True,
                "success": all_succeeded,
                "trades": execution_results,
            }
            
            return f"Rebalance execution complete for portfolio {params.portfolio_id}. " + \
                   f"All trades succeeded: {all_succeeded}. " + \
                   f"Details: {json.dumps(result_summary, indent=2)}"
            
        except Exception as e:
            logger.error(f"Error executing rebalance: {str(e)}")
            return f"Error executing rebalance: {str(e)}"
    
    @create_action(
        name="simulate-rebalance",
        description="Simulate a portfolio rebalance with custom allocations",
        schema=SimulateRebalanceParams
    )
    def simulate_rebalance(self, wallet_provider: EvmWalletProvider, args: Dict[str, Any]) -> str:
        """
        Simulate a portfolio rebalance with custom allocations
        
        This is useful for testing different allocation strategies before executing
        """
        params = SimulateRebalanceParams(**args)
        
        try:
            # Get current portfolio
            portfolio = asyncio.run(self.intelligence_engine.get_portfolio(
                params.user_id,
                params.portfolio_id
            ))
            
            # Calculate trades needed for the target allocations
            current_values = {
                asset["symbol"]: asset["value"]
                for asset in portfolio.get("assets", [])
            }
            current_weights = {
                asset["symbol"]: asset["weight"]
                for asset in portfolio.get("assets", [])
            }
            
            # Calculate total portfolio value
            total_value = sum(current_values.values())
            
            # Calculate trades
            trades = []
            for symbol, target_weight in params.target_allocations.items():
                current_weight = current_weights.get(symbol, 0)
                current_value = current_values.get(symbol, 0)
                
                target_value = total_value * target_weight
                value_change = target_value - current_value
                
                # Get current price
                current_price = None
                for asset in portfolio.get("assets", []):
                    if asset["symbol"] == symbol:
                        current_price = asset.get("price", 0)
                        break
                        
                if not current_price or current_price <= 0:
                    # Skip assets with no price data
                    continue
                    
                amount_change = value_change / current_price
                
                trades.append({
                    "symbol": symbol,
                    "amount": amount_change,
                    "value": value_change,
                    "price": current_price,
                    "weight_change": target_weight - current_weight
                })
                
            # Calculate estimated costs (fees)
            fee_rate = self.config.get("FEE_RATE", 0.001)  # Default 0.1%
            estimated_fees = sum(abs(t["value"]) * fee_rate for t in trades)
            
            # Get current market condition
            market_condition = asyncio.run(self.strategy_engine.get_market_condition())
            
            # Get validation from reviewer
            validation = asyncio.run(self.trade_reviewer.validate_rebalance_plan(
                [{"asset": t["symbol"], "action": "increase" if t["amount"] > 0 else "decrease"}
                for t in trades if t["amount"] != 0],
                market_condition
            ))
            
            result = {
                "portfolio_id": params.portfolio_id,
                "total_value": total_value,
                "current_weights": current_weights,
                "target_weights": params.target_allocations,
                "trades": trades,
                "estimated_fees": estimated_fees,
                "market_condition": market_condition,
                "validation": validation
            }
            
            return f"Rebalance simulation complete for portfolio {params.portfolio_id}. " + \
                   f"Estimated fees: {estimated_fees}. " + \
                   f"Market condition: {market_condition}. " + \
                   f"Details: {json.dumps(result, indent=2)}"
            
        except Exception as e:
            logger.error(f"Error simulating rebalance: {str(e)}")
            return f"Error simulating rebalance: {str(e)}"
    
    @create_action(
        name="get-performance",
        description="Get performance metrics and recommendations for a portfolio",
        schema=GetPerformanceParams
    )
    def get_performance(self, wallet_provider: EvmWalletProvider, args: Dict[str, Any]) -> str:
        """Get performance metrics and recommendations"""
        params = GetPerformanceParams(**args)
        
        try:
            # Get performance data
            performance = asyncio.run(self.performance_analyzer.analyze_performance(
                params.portfolio_id
            ))
            
            # If recommendations requested, generate report
            if params.include_recommendations:
                report = asyncio.run(self.performance_analyzer.generate_performance_report(
                    params.days
                ))
                performance["report"] = report
                
            return f"Performance analysis complete for last {params.days} days. " + \
                   f"Details: {json.dumps(performance, indent=2)}"
            
        except Exception as e:
            logger.error(f"Error getting performance: {str(e)}")
            return f"Error getting performance: {str(e)}"
    
    @create_action(
        name="enable-auto-rebalance-from-text",
        description="Enable automatic portfolio rebalancing from natural language request",
        schema=EnableAutoRebalanceParams
    )
    def enable_auto_rebalance_from_text(self, wallet_provider: EvmWalletProvider, args: Dict[str, Any]) -> str:
        """Enable automatic rebalancing based on natural language request"""
        params = EnableAutoRebalanceParams(**args)
        user_id = self.context.get("user_id", "current_user")
        
        logger.info(f"Enabling auto-rebalance for user {user_id}, portfolio {params.portfolio_name}")
        
        try:
            # Convert frequency to check interval
            interval_mapping = {
                "hourly": 3600,
                "daily": 86400,
                "weekly": 604800,
                "monthly": 2592000
            }
            check_interval = interval_mapping.get(params.frequency.lower(), 86400)  # Default to daily
            
            # Resolve portfolio name to ID
            portfolio_id = asyncio.run(self._resolve_portfolio_name(user_id, params.portfolio_name))
            if not portfolio_id:
                return f"Could not find portfolio named '{params.portfolio_name}'"
            
            # Update portfolio settings - use 1 for true in SQLite
            updated = asyncio.run(self.db_manager.update_portfolio(
                portfolio_id,
                {
                    "auto_rebalance": 1,  # SQLite boolean as integer
                    "max_slippage": params.max_slippage,
                    "check_interval": check_interval
                }
            ))
            
            if updated:
                # Get human-readable frequency
                human_frequency = params.frequency.lower()
                return f"Automatic rebalancing enabled for your {params.portfolio_name} portfolio. " + \
                        f"It will be checked {human_frequency} with max slippage of {params.max_slippage}%."
            else:
                return f"Could not enable automatic rebalancing for {params.portfolio_name} portfolio."
        except Exception as e:
            logger.error(f"Error enabling auto-rebalance: {str(e)}")
            return f"Error enabling auto-rebalance: {str(e)}"

    @create_action(
        name="disable-auto-rebalance-from-text",
        description="Disable automatic portfolio rebalancing from natural language request",
        schema=DisableAutoRebalanceParams
    )
    def disable_auto_rebalance_from_text(self, wallet_provider: EvmWalletProvider, args: Dict[str, Any]) -> str:
        """Disable automatic rebalancing based on natural language request"""
        params = DisableAutoRebalanceParams(**args)
        user_id = self.context.get("user_id", "current_user")
        
        logger.info(f"Disabling auto-rebalance for user {user_id}, portfolio {params.portfolio_name}")
        
        try:
            # Resolve portfolio name to ID
            portfolio_id = asyncio.run(self._resolve_portfolio_name(user_id, params.portfolio_name))
            if not portfolio_id:
                return f"Could not find portfolio named '{params.portfolio_name}'"
            
            # Update portfolio settings - use 0 for false in SQLite
            updated = asyncio.run(self.db_manager.update_portfolio(
                portfolio_id,
                {
                    "auto_rebalance": 0  # SQLite boolean as integer
                }
            ))
            
            if updated:
                return f"Automatic rebalancing disabled for your {params.portfolio_name} portfolio."
            else:
                return f"Could not disable automatic rebalancing for {params.portfolio_name} portfolio."
        except Exception as e:
            logger.error(f"Error disabling auto-rebalance: {str(e)}")
            return f"Error disabling auto-rebalance: {str(e)}"

    @create_action(
        name="get-rebalancing-status",
        description="Get the current status of the rebalancing strategy",
        schema=GetRebalancingStatusParams
    )
    def get_rebalancing_status(self, wallet_provider: EvmWalletProvider, args: Dict[str, Any]) -> str:
        """Get current rebalancing status for a portfolio"""
        params = GetRebalancingStatusParams(**args)
        user_id = self.context.get("user_id", "current_user")
        
        try:
            # Resolve portfolio name to ID
            portfolio_id = asyncio.run(self._resolve_portfolio_name(user_id, params.portfolio_name))
            if not portfolio_id:
                return f"Could not find portfolio named '{params.portfolio_name}'"
            
            # Get portfolio details
            portfolio = asyncio.run(self._get_portfolio_by_id(portfolio_id))
            if not portfolio:
                return f"Could not retrieve details for portfolio {params.portfolio_name}"
            
            # Check auto-rebalance status
            is_active = portfolio.get("auto_rebalance", 0) == 1
            check_interval = portfolio.get("check_interval", 86400)
            max_slippage = portfolio.get("max_slippage", 1.0)
            
            # Convert check interval to human-readable format
            frequency = "daily"
            if check_interval <= 3600:
                frequency = "hourly"
            elif check_interval <= 86400:
                frequency = "daily"
            elif check_interval <= 604800:
                frequency = "weekly"
            else:
                frequency = "monthly"
            
            if is_active:
                return f"Automatic rebalancing is active for your {params.portfolio_name} portfolio. " + \
                      f"It is checked {frequency} with maximum slippage of {max_slippage}%."
            else:
                return f"Automatic rebalancing is not active for your {params.portfolio_name} portfolio."
        except Exception as e:
            logger.error(f"Error getting rebalancing status: {str(e)}")
            return f"Error getting rebalancing status: {str(e)}"
    
    async def _execute_buy(self, user_id: str, symbol: str, amount: float, max_slippage_percent: float) -> Dict[str, Any]:
        """Execute a buy trade using the most appropriate method"""
        try:
            # Determine the best execution method
            if self._should_use_limit_order(symbol, amount):
                return await self._execute_limit_buy(symbol, amount, max_slippage_percent)
            elif self._should_use_swap(symbol):
                return await self._execute_swap_buy(symbol, amount, max_slippage_percent)
            else:
                return await self._execute_market_buy(symbol, amount, max_slippage_percent)
        except Exception as e:
            logger.error(f"Error executing buy for {symbol}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _execute_sell(self, user_id: str, symbol: str, amount: float, max_slippage_percent: float) -> Dict[str, Any]:
        """Execute a sell trade using the most appropriate method"""
        try:
            # Determine the best execution method
            if self._should_use_limit_order(symbol, amount):
                return await self._execute_limit_sell(symbol, amount, max_slippage_percent)
            elif self._should_use_swap(symbol):
                return await self._execute_swap_sell(symbol, amount, max_slippage_percent)
            else:
                return await self._execute_market_sell(symbol, amount, max_slippage_percent)
        except Exception as e:
            logger.error(f"Error executing sell for {symbol}: {str(e)}")
            return {"success": False, "error": str(e)}
        
    async def _resolve_portfolio_name(self, user_id: str, portfolio_name: str) -> Optional[int]:
        """Helper function to convert portfolio name to ID"""
        # Get user's portfolios
        portfolios = await self._get_user_portfolios(user_id)
        
        # Look for exact name match
        for portfolio in portfolios:
            if portfolio.get("name", "").lower() == portfolio_name.lower():
                return portfolio.get("id")
        
        # If not found and portfolio_name is "main" or "default", return first portfolio
        if portfolio_name.lower() in ["main", "default"] and portfolios:
            return portfolios[0].get("id")
        
        # No matching portfolio found
        return None
    
    async def _get_user_portfolios(self, user_id: str) -> List[Dict[str, Any]]:
        """Get portfolios for a user"""
        # This should be implemented based on how you retrieve user portfolios
        # Using your existing db_manager implementation
        return await self.db_manager.get_user_portfolios(user_id)
    
    async def _get_portfolio_by_id(self, portfolio_id: int) -> Optional[Dict[str, Any]]:
        """Get portfolio by ID"""
        # This should be implemented based on how you retrieve portfolios
        # Using your existing db_manager implementation
        return await self.db_manager.get_portfolio(portfolio_id)

    def _should_use_limit_order(self, symbol: str, amount: float) -> bool:
        """Determine if we should use a limit order based on symbol and amount"""
        # For large trades (reduce market impact)
        if amount > self.config.get("large_trade_threshold", 1000):
            return True
        
        # For highly liquid markets where limit orders are likely to fill
        highly_liquid_markets = self.config.get("highly_liquid_markets", ["BTC", "ETH"])
        if symbol in highly_liquid_markets:
            return True
        
        return False

    def _should_use_swap(self, symbol: str) -> bool:
        """Determine if we should use a swap based on symbol"""
        # For tokens that don't have a direct market or have low liquidity
        direct_markets = self.config.get("direct_markets", ["BTC-USDC", "ETH-USDC"])
        
        # Check if this symbol has a direct market
        has_direct_market = any(symbol in market for market in direct_markets)
        
        return not has_direct_market

    async def _execute_limit_buy(self, symbol: str, amount: float, max_slippage_percent: float) -> Dict[str, Any]:
        """Execute a limit buy order through Kuru"""
        # Determine market details
        base_token, quote_token = self._get_market_tokens(symbol)
        market_id = self._get_market_id(symbol)
        
        # Calculate order price with some buffer below current price for faster fill
        current_price = await self._get_current_price(symbol)
        limit_price = current_price * (1 - (max_slippage_percent / 200))  # Half the slippage as buffer
        
        # Prepare parameters for limit order
        args = {
            "from_token": quote_token,
            "to_token": base_token,
            "amount_in": amount,
            "price": limit_price,
            "post_only": False,
            "market_id": market_id
        }
        
        # Execute the limit order
        result = self.kuru_provider.place_limit_order(self.wallet_provider, args)
        return result

    async def _execute_market_buy(self, symbol: str, amount: float, max_slippage_percent: float) -> Dict[str, Any]:
        """Execute a market buy order through Kuru"""
        # Determine market details
        base_token, quote_token = self._get_market_tokens(symbol)
        market_id = self._get_market_id(symbol)
        
        # Prepare parameters for market order
        args = {
            "from_token": quote_token,
            "to_token": base_token,
            "amount_in": amount,
            "slippage_percentage": max_slippage_percent,
            "market_id": market_id
        }
        
        # Execute the swap (which performs a market order)
        result = self.kuru_provider.swap(self.wallet_provider, args)
        return result

    async def _execute_swap_buy(self, symbol: str, amount: float, max_slippage_percent: float) -> Dict[str, Any]:
        """Execute a swap when no direct market exists"""
        # For tokens without direct markets, always use swap
        # This is similar to market buy but may use different parameters
        
        # Determine tokens
        to_token = symbol.lower()
        from_token = "usdc"  # Default quote token
        
        # Prepare parameters for swap
        args = {
            "from_token": from_token,
            "to_token": to_token,
            "amount_in": amount,
            "slippage_percentage": max_slippage_percent,
            "market_id": self._get_best_route_market(from_token, to_token)
        }
        
        # Execute the swap
        result = self.kuru_provider.swap(self.wallet_provider, args)
        return result

    # Similar implementations for sell operations...
    async def _execute_limit_sell(self, symbol: str, amount: float, max_slippage_percent: float) -> Dict[str, Any]:
        """Execute a limit sell order through Kuru"""
        # Implementation similar to limit buy but reversed
        pass

    async def _execute_market_sell(self, symbol: str, amount: float, max_slippage_percent: float) -> Dict[str, Any]:
        """Execute a market sell order through Kuru"""
        # Implementation similar to market buy but reversed
        pass

    async def _execute_swap_sell(self, symbol: str, amount: float, max_slippage_percent: float) -> Dict[str, Any]:
        """Execute a swap sell when no direct market exists"""
        # Implementation similar to swap buy but reversed
        pass

    def _get_market_tokens(self, symbol: str) -> Tuple[str, str]:
        """Get base and quote tokens for a symbol"""
        # Default mapping
        markets = {
            "BTC": ("native", "usdc"),
            "ETH": ("native", "usdc"),
            "MON": ("native", "usdc"),
            "USDC": ("usdc", "native"),
            # Add more mappings as needed
        }
        
        return markets.get(symbol.upper(), ("unknown", "unknown"))

    def _get_market_id(self, symbol: str) -> str:
        """Get market ID for a symbol"""
        # Default mapping
        market_ids = {
            "BTC": "btc-usdc",
            "ETH": "eth-usdc",
            "MON": "mon-usdc",
            # Add more mappings as needed
        }
        
        return market_ids.get(symbol.upper(), "unknown")

    async def _get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        # This could query from a price feed or use Kuru orderbook
        # For now, simplistic implementation
        try:
            market_id = self._get_market_id(symbol)
            orderbook = self.kuru_provider.get_orderbook(self.wallet_provider, {
                "market_id": market_id
            })
            
            # Parse the orderbook response to get the price
            # This is a simplistic approach - would need proper parsing in production
            if "asks" in orderbook and len(orderbook["asks"]) > 0:
                return float(orderbook["asks"][0]["price"])
            else:
                # Fallback
                return 0.0
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {str(e)}")
            return 0.0

    def _get_best_route_market(self, from_token: str, to_token: str) -> str:
        """Determine best market for routing a swap"""
        # Simple implementation - in production would use a router or path finding
        if from_token == "usdc" and to_token == "native":
            return "mon-usdc"
        elif from_token == "native" and to_token == "usdc":
            return "mon-usdc"
        else:
            # Default to a known liquid market
            return "mon-usdc"

    # Add setter methods for late binding
    def set_intelligence_engine(self, intelligence_engine: IntelligenceEngine):
        self.intelligence_engine = intelligence_engine
    
    def set_strategy_engine(self, strategy_engine: StrategyEngine):
        self.strategy_engine = strategy_engine
    
    def set_trade_reviewer(self, trade_reviewer: TradeReviewer):
        self.trade_reviewer = trade_reviewer
    
    def set_performance_analyzer(self, performance_analyzer: PerformanceAnalyzer):
        self.performance_analyzer = performance_analyzer
    
    def set_db_manager(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

def rebalancer_action_provider(
    wallet_provider: Optional[EvmWalletProvider] = None,
    intelligence_engine = None,
    strategy_engine = None,
    trade_reviewer = None,
    performance_analyzer = None,
    db_manager = None,
    kuru_provider = None,
    context: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None
) -> RebalancerActionProvider:
    """Create and return a RebalancerActionProvider instance
    
    All dependencies can be injected later using setter methods if not provided.
    """
    return RebalancerActionProvider(
        wallet_provider=wallet_provider,
        intelligence_engine=intelligence_engine,
        strategy_engine=strategy_engine,
        trade_reviewer=trade_reviewer,
        performance_analyzer=performance_analyzer,
        db_manager=db_manager,
        kuru_provider=kuru_provider,
        context=context,
        config=config
    ) 


