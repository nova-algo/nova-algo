import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, TYPE_CHECKING
from datetime import datetime, timedelta

from .risk_manager import RiskManager
from .yield_optimizer import YieldOptimizer
from .wormhole import WormholeService

# Use TYPE_CHECKING to break circular import
if TYPE_CHECKING:
    from ..intelligence.intelligence_engine import IntelligenceEngine

logger = logging.getLogger(__name__)

class StrategyEngine:
    """
    Core strategy execution engine that implements rebalancing execution
    based on decisions from the Intelligence Engine, focusing purely on
    statistical analysis as recommended by Rose Heart.
    """
    
    def __init__(self):
        self.intelligence_engine = None  # Will be set later
        self.risk_manager = None
        self.yield_optimizer = None
        self.wormhole_service = None
        self.db_manager = None
        self.config = None
        
        # Asset-specific profiles following Rose Heart's recommendation
        self.asset_profiles = {
            "BTC": {
                "below_median_weight": 0.30,  # Higher weight due to BTC tendency to remain below median
                "volatility_threshold": 0.18,  # Higher threshold for BTC
                "manipulation_detection_threshold": 0.65,  # Lower threshold (established asset)
                "min_allocation": 0.05,
                "max_allocation": 0.30
            },
            "ETH": {
                "below_median_weight": 0.20,
                "volatility_threshold": 0.22,  # Higher threshold for ETH's volatility patterns
                "manipulation_detection_threshold": 0.65,
                "min_allocation": 0.05,
                "max_allocation": 0.30
            },
            "USDC": {
                "regulatory_risk_weight": 0.15,
                "volatility_threshold": 0.01,
                "manipulation_detection_threshold": 0.80,
                "min_allocation": 0.10,
                "max_allocation": 0.50
            },
            "USDT": {
                "regulatory_risk_weight": 0.20,  # Higher regulatory risk than USDC
                "volatility_threshold": 0.01,
                "manipulation_detection_threshold": 0.80,
                "min_allocation": 0.05,
                "max_allocation": 0.40
            },
            "SOL": {
                "below_median_weight": 0.15,
                "volatility_threshold": 0.25,  # Higher volatility
                "manipulation_detection_threshold": 0.70,
                "min_allocation": 0.0,
                "max_allocation": 0.20
            },
            # Default profile for other assets
            "DEFAULT": {
                "below_median_weight": 0.15,
                "volatility_threshold": 0.20,
                "manipulation_detection_threshold": 0.75,
                "min_allocation": 0.0,
                "max_allocation": 0.15
            }
        }
    
    def set_intelligence_engine(self, intelligence_engine):
        """Set the intelligence engine after initialization"""
        self.intelligence_engine = intelligence_engine
    
    async def analyze_portfolio_statistics(self, portfolio_id: int) -> Dict[str, Any]:
        """
        Pure statistical analysis of portfolio without decision making.
        This provides metrics for the Intelligence Engine to consume.
        """
        try:
            # Get portfolio data
            portfolio = await self.db_manager.get_portfolio(portfolio_id)
            
            # Get risk assessment - purely statistical as Rose Heart advised
            risk_assessment = await self.risk_manager.assess_portfolio_risk(portfolio_id)
            
            # Calculate asset metrics
            asset_metrics = await self._calculate_asset_metrics(portfolio)
            
            # Calculate portfolio metrics
            portfolio_metrics = {
                "portfolio_id": portfolio_id,
                "total_value": portfolio.get("total_value", 0),
                "risk_level": risk_assessment.get("risk_level", "moderate"),
                "volatility": risk_assessment.get("volatility", 0),
                "sharpe_ratio": risk_assessment.get("sharpe_ratio", 0),
                "drawdown": risk_assessment.get("max_drawdown", 0),
                "asset_metrics": asset_metrics
            }
            
            # Check circuit breakers
            circuit_breakers = self._check_circuit_breakers(portfolio_metrics)
            portfolio_metrics["circuit_breakers"] = circuit_breakers
            
            return portfolio_metrics
        except Exception as e:
            logger.error(f"Error analyzing portfolio statistics: {str(e)}")
            return {
                "portfolio_id": portfolio_id,
                "error": str(e),
                "message": "Error analyzing portfolio statistics"
            }
    
    async def execute_rebalance(self, user_id: str, portfolio_id: int, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute portfolio rebalancing based on recommendations from Intelligence Engine.
        This focuses purely on execution, not decision making.
        """
        try:
            # Validate recommendation
            if not recommendation.get("rebalance_recommended", False):
                return {
                    "portfolio_id": portfolio_id,
                    "success": False,
                    "message": "Rebalancing not recommended",
                    "reason": recommendation.get("reason", "Unknown")
                }
            
            # Check circuit breakers
            portfolio_stats = await self.analyze_portfolio_statistics(portfolio_id)
            if portfolio_stats.get("circuit_breakers", {}).get("active", False):
                return {
                    "portfolio_id": portfolio_id,
                    "success": False,
                    "message": "Rebalancing paused",
                    "reason": portfolio_stats["circuit_breakers"].get("reason", "Circuit breaker active")
                }
            
            # Get target allocations from recommendation
            target_allocations = recommendation.get("target_allocations", {})
            
            # Get current portfolio 
            portfolio = await self.db_manager.get_portfolio(portfolio_id)
            
            # Calculate required trades
            trades = await self._calculate_required_trades(portfolio, target_allocations)
            
            # Execute trades
            executed_trades = await self._execute_trades(trades)
            
            # Update portfolio in database
            await self.db_manager.update_portfolio_after_rebalance(
                portfolio_id, 
                executed_trades, 
                target_allocations
            )
            
            return {
                "portfolio_id": portfolio_id,
                "success": True,
                "message": "Portfolio rebalanced successfully",
                "trades_executed": executed_trades,
                "new_allocations": target_allocations
            }
        except Exception as e:
            logger.error(f"Error executing rebalance: {str(e)}")
            return {
                "portfolio_id": portfolio_id,
                "success": False,
                "error": str(e),
                "message": "Error executing rebalance"
            }
    
    async def calculate_rebalancing_costs(self, portfolio) -> Dict[str, float]:
        """
        Calculate costs of rebalancing (transaction fees, slippage, etc.)
        This is used by the Intelligence Engine for cost-benefit analysis.
        """
        # Simplified implementation
        assets = portfolio.get("assets", [])
        total_value = sum(asset.get("value", 0) for asset in assets)
        
        # Estimate trading fees as 0.1% of total portfolio value
        trading_fees = total_value * 0.001
        
        # Estimate gas fees for cross-chain operations
        gas_fees = 10  # Fixed amount in USD
        
        # Estimate slippage based on asset liquidity and trade size
        slippage_cost = total_value * 0.001  # 0.1% slippage
        
        return {
            "trading_fees": trading_fees,
            "gas_fees": gas_fees,
            "slippage_cost": slippage_cost,
            "total_cost": trading_fees + gas_fees + slippage_cost
        }
    
    async def _calculate_asset_metrics(self, portfolio) -> Dict[str, Any]:
        """Calculate statistical metrics for each asset in the portfolio"""
        asset_metrics = {}
        
        for asset in portfolio.get("assets", []):
            symbol = asset.get("symbol")
            
            # Get asset profile or use default
            profile = self.asset_profiles.get(symbol, self.asset_profiles["DEFAULT"])
            
            # Get historical data
            historical_data = await self.db_manager.get_asset_historical_data(symbol)
            
            # Calculate trend
            trend = self._analyze_price_trend(symbol, historical_data)
            
            # Calculate volatility
            volatility = self._calculate_asset_volatility(historical_data)
            
            # Calculate below median metric
            below_median = self._calculate_below_median(historical_data)
            
            asset_metrics[symbol] = {
                "trend": trend,
                "volatility": volatility,
                "below_median": below_median,
                "profile": profile
            }
        
        return asset_metrics
    
    def _analyze_price_trend(self, symbol: str, historical_data: List[Dict[str, Any]], window: int = 24) -> str:
        """
        Analyze recent price trend similar to AutoTradeBot
        Returns: "UP", "DOWN", or "SIDEWAYS"
        """
        if not historical_data or len(historical_data) < window:
            return "SIDEWAYS"
            
        recent_prices = [point.get("price", 0) for point in historical_data[-window:]]
        if not recent_prices or len(recent_prices) < 2:
            return "SIDEWAYS"
            
        price_change = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        
        if abs(price_change) < 0.01:  # Less than 1% change
            return "SIDEWAYS"
        return "UP" if price_change > 0 else "DOWN"
    
    def _calculate_asset_volatility(self, historical_data: List[Dict[str, Any]], window: int = 30) -> float:
        """Calculate volatility for an asset using standard deviation of returns"""
        if not historical_data or len(historical_data) < window:
            return 0.0
            
        prices = [point.get("price", 0) for point in historical_data[-window:]]
        if not prices or len(prices) < 2:
            return 0.0
            
        # Calculate daily returns
        returns = [(prices[i] / prices[i-1]) - 1 for i in range(1, len(prices))]
        
        # Calculate standard deviation
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        
        return (variance ** 0.5) * (252 ** 0.5)  # Annualized volatility
    
    def _calculate_below_median(self, historical_data: List[Dict[str, Any]], window: int = 60) -> float:
        """
        Calculate how often price stays below median
        This is important for BTC as Rose Heart mentioned it tends to stay below median
        """
        if not historical_data or len(historical_data) < window:
            return 0.5  # Default 50%
            
        prices = [point.get("price", 0) for point in historical_data[-window:]]
        if not prices:
            return 0.5
            
        median_price = sorted(prices)[len(prices) // 2]
        below_count = sum(1 for price in prices if price < median_price)
        
        return below_count / len(prices)
    
    def _check_circuit_breakers(self, portfolio_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implement circuit breakers to pause rebalancing during extreme market conditions
        as recommended by Rose Heart
        """
        # Check for extreme market volatility
        if portfolio_metrics.get("volatility", 0) > self.config.get("EXTREME_VOLATILITY_THRESHOLD", 0.05):
            return {
                "active": True,
                "reason": f"Extreme portfolio volatility detected: {portfolio_metrics['volatility']:.2%}"
            }
        
        # Check for excessive drawdown
        if portfolio_metrics.get("drawdown", 0) > self.config.get("EXTREME_DRAWDOWN_THRESHOLD", 0.15):
            return {
                "active": True,
                "reason": f"Excessive drawdown detected: {portfolio_metrics['drawdown']:.2%}"
            }
        
        # Check asset-specific circuit breakers
        for symbol, metrics in portfolio_metrics.get("asset_metrics", {}).items():
            profile = metrics.get("profile", {})
            volatility_threshold = profile.get("volatility_threshold", 0.20)
            
            if metrics.get("volatility", 0) > volatility_threshold:
                return {
                    "active": True,
                    "reason": f"Extreme volatility detected for {symbol}: {metrics['volatility']:.2%}"
                }
        
        return {
            "active": False,
            "reason": None
        }
    
    async def _calculate_required_trades(self, portfolio: Dict[str, Any], target_allocations: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Calculate required trades to achieve target allocations
        Implementing Rose Heart's 5% minimum deviation threshold
        """
        trades = []
        
        assets = portfolio.get("assets", [])
        total_value = portfolio.get("total_value", 0)
        
        if not total_value or not assets:
            return []
        
        current_allocations = {
            asset["symbol"]: asset["value"] / total_value
            for asset in assets
        }
        
        for symbol, target_allocation in target_allocations.items():
            current_allocation = current_allocations.get(symbol, 0)
            
            # Calculate absolute deviation as percentage of portfolio
            deviation = abs(target_allocation - current_allocation)
            
            # Only rebalance if deviation exceeds threshold (Rose Heart recommended 5%)
            if deviation > self.config.get("MIN_REBALANCE_THRESHOLD", 0.05):
                # Find asset in portfolio
                asset = next((a for a in assets if a["symbol"] == symbol), None)
                
                current_value = asset["value"] if asset else 0
                target_value = total_value * target_allocation
                trade_value = target_value - current_value
                
                trades.append({
                    "symbol": symbol,
                    "action": "buy" if trade_value > 0 else "sell",
                    "current_value": current_value,
                    "target_value": target_value,
                    "trade_value": abs(trade_value),
                    "current_allocation": current_allocation,
                    "target_allocation": target_allocation,
                    "deviation": deviation
                })
        
        return trades
    
    async def _execute_trades(self, trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute required trades
        This would integrate with actual exchange APIs in production
        """
        # Placeholder implementation - in production, would connect to exchanges
        executed_trades = []
        
        for trade in trades:
            # Simulate successful execution
            executed_trade = {
                **trade,
                "status": "executed",
                "execution_price": None,  # Would come from exchange
                "timestamp": datetime.now().isoformat(),
                "transaction_id": f"sim_{trade['symbol']}_{int(datetime.now().timestamp())}"
            }
            
            executed_trades.append(executed_trade)
            logger.info(f"Executed trade: {trade['action']} {trade['symbol']} worth ${trade['trade_value']:.2f}")
        
        return executed_trades
    
    async def record_trade_performance(self, portfolio_id: int, trades: List[Dict[str, Any]]) -> None:
        """Record trade performance for future analysis"""
        # This would be implemented in production to record trade outcomes
        # for performance analysis and weights adjustment
        pass
