"""
PortfolioActionProvider

Provides actions for portfolio analysis and insights without execution,
implementing the AgentKit action provider pattern.
"""
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Type, Union, cast
from pydantic import BaseModel, Field, root_validator, validator
from decimal import Decimal

from coinbase_agentkit.action_providers.action_decorator import create_action
from coinbase_agentkit.action_providers.action_provider import ActionProvider
from coinbase_agentkit.network import Network
from coinbase_agentkit.wallet_providers import EvmWalletProvider

from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from rebalancr.intelligence.intelligence_engine import IntelligenceEngine
else:
    # For runtime, just use Any
    IntelligenceEngine = Any


from rebalancr.strategy.engine import StrategyEngine
from rebalancr.strategy.risk_manager import RiskManager
from rebalancr.strategy.yield_optimizer import YieldOptimizer
from rebalancr.performance.analyzer import PerformanceAnalyzer

logger = logging.getLogger(__name__)

# Supported networks
SUPPORTED_NETWORKS = [1, 56, 137, 42161, 10]  # Ethereum, BSC, Polygon, Arbitrum, Optimism

class AnalyzePortfolioParams(BaseModel):
    """Parameters for portfolio analysis"""
    portfolio_id: int
    user_id: str = "current_user"
    include_sentiment: bool = True
    include_manipulation_check: bool = True
    detailed: bool = False

class AssessRiskParams(BaseModel):
    """Parameters for risk assessment"""
    portfolio_id: int
    user_id: str = "current_user"
    timeframe_days: int = Field(ge=1, le=365, default=30)
    include_sentiment_impact: bool = True
    
    @validator('timeframe_days')
    def validate_timeframe(cls, v):
        if v < 1 or v > 365:
            raise ValueError("Timeframe must be between 1 and 365 days")
        return v

class FindYieldParams(BaseModel):
    """Parameters for yield opportunity finding"""
    portfolio_id: int
    user_id: str = "current_user"
    min_apy: float = Field(ge=0, le=100, default=0)
    risk_tolerance: str = Field(default="moderate")
    include_sentiment_filter: bool = True
    
    @validator('risk_tolerance')
    def validate_risk_tolerance(cls, v):
        allowed = ["conservative", "moderate", "aggressive"]
        if v.lower() not in allowed:
            raise ValueError(f"Risk tolerance must be one of: {', '.join(allowed)}")
        return v.lower()
    
    @validator('min_apy')
    def validate_min_apy(cls, v):
        if v < 0 or v > 100:
            raise ValueError("Minimum APY must be between 0 and 100%")
        return v

class SimulateRebalanceParams(BaseModel):
    """Parameters for simulating portfolio rebalance"""
    portfolio_id: int
    user_id: str = "current_user"
    target_allocations: Dict[str, float] = Field(default_factory=dict)
    time_horizon_days: int = Field(ge=1, le=365, default=30)
    
    @root_validator(skip_on_failure=True)
    def validate_allocations(cls, v, values):
            allocations = values.get('target_allocations', {})
            if not allocations:
                raise ValueError('Target allocations must be provided')
            
            total = sum(allocations.values())
            if abs(total - 1.0) > 0.01:  # Allow small rounding errors
                raise ValueError(f'Target allocations must sum to 1.0 (got {total})')
            
            return values
        
    @validator('time_horizon_days')
    def validate_time_horizon(cls, v):
        if v < 1 or v > 365:
            raise ValueError("Time horizon must be between 1 and 365 days")
        return v

class PortfolioActionProvider(ActionProvider):
    """
    Action provider for portfolio analysis and insights without execution
    
    Provides analytical actions focusing on risk assessment, yield opportunities,
    and portfolio simulation, as recommended by Rose Heart.
    """
    
    def __init__(
        self,
        wallet_provider: EvmWalletProvider,
        intelligence_engine: IntelligenceEngine,
        strategy_engine: StrategyEngine,
        risk_manager: RiskManager,
        yield_optimizer: YieldOptimizer,
        performance_analyzer: PerformanceAnalyzer,
        db_manager,
        config: Dict[str, Any]
    ):
        super().__init__(
            name="portfolio-action", 
            action_providers=[]  # Empty list since actions are defined using decorators 
        )
        self.wallet_provider = wallet_provider
        self.intelligence_engine = intelligence_engine
        self.strategy_engine = strategy_engine
        self.risk_manager = risk_manager
        self.yield_optimizer = yield_optimizer
        self.performance_analyzer = performance_analyzer
        self.db_manager = db_manager
        self.config = config
    
    def supports_network(self, network_id: int) -> bool:
        """Check if the provider supports the given network ID"""
        return network_id in SUPPORTED_NETWORKS
    
    @create_action(
        name="analyze-portfolio",
        description="Analyze a portfolio and provide comprehensive insights including sentiment analysis",
        schema=AnalyzePortfolioParams
    )
    async def analyze_portfolio(self, params: AnalyzePortfolioParams) -> Dict[str, Any]:
        """
        Analyze portfolio and provide comprehensive insights
        
        Combines statistical analysis with sentiment data from Allora, following
        Rose Heart's dual-system approach.
        """
        try:
            # Get portfolio data
            portfolio = await self.db_manager.get_portfolio(params.portfolio_id)
            
            # Get sentiment-enhanced analysis from Intelligence Engine
            analysis = await self.intelligence_engine.analyze_portfolio(
                user_id=params.user_id,
                portfolio_id=params.portfolio_id
            )
            
            # Get statistical metrics from Strategy Engine
            stats = await self.strategy_engine.analyze_portfolio_statistics(params.portfolio_id)
            
            # Get performance metrics
            performance = await self.performance_analyzer.get_portfolio_performance(
                portfolio_id=params.portfolio_id,
                include_sentiment_impact=params.include_sentiment
            )
            
            # Prepare detailed or summary response
            if params.detailed:
                result = {
                    "portfolio_id": params.portfolio_id,
                    "total_value": portfolio.get("total_value", 0),
                    "asset_allocation": {asset["symbol"]: asset["percentage"] / 100 for asset in portfolio.get("assets", [])},
                    "intelligence_analysis": analysis,
                    "statistical_metrics": stats,
                    "performance_metrics": performance,
                    "rebalance_recommendation": analysis.get("rebalance_recommended", False),
                    "reason": analysis.get("reason", ""),
                    "insights": self._generate_insights(analysis, stats, performance)
                }
            else:
                result = {
                    "portfolio_id": params.portfolio_id,
                    "total_value": portfolio.get("total_value", 0),
                    "risk_level": stats.get("risk_level", "moderate"),
                    "rebalance_recommended": analysis.get("rebalance_recommended", False),
                    "reason": analysis.get("reason", ""),
                    "insights": self._generate_insights(analysis, stats, performance),
                    "performance_summary": {
                        "30d_return": performance.get("return_30d", 0),
                        "sentiment_accuracy": performance.get("sentiment_accuracy", 0)
                    }
                }
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing portfolio: {str(e)}")
            return {
                "error": str(e),
                "message": "Error analyzing portfolio"
            }
    
    @create_action(
        name="assess-risk",
        description="Provide detailed risk assessment with market sentiment influences",
        schema=AssessRiskParams
    )
    async def assess_risk(self, params: AssessRiskParams) -> Dict[str, Any]:
        """
        Detailed risk assessment with sentiment context
        
        Provides statistical risk metrics enhanced with market sentiment data, 
        following Rose Heart's recommendation to keep numerical calculations statistical.
        """
        try:
            # Get full risk assessment from Risk Manager (purely statistical)
            risk_assessment = await self.risk_manager.assess_portfolio_risk(params.portfolio_id)
            
            # Get sentiment analysis from Intelligence Engine if requested
            sentiment_impact = {}
            if params.include_sentiment_impact:
                # Get portfolio data
                portfolio = await self.db_manager.get_portfolio(params.portfolio_id)
                
                # Get sentiment for each asset
                asset_sentiments = await self.intelligence_engine.get_asset_sentiments(
                    assets=[asset["symbol"] for asset in portfolio.get("assets", [])],
                    days=params.timeframe_days
                )
                
                # Get manipulation detection results
                manipulation_check = await self.intelligence_engine.check_manipulation(
                    assets=[asset["symbol"] for asset in portfolio.get("assets", [])]
                )
                
                sentiment_impact = {
                    "asset_sentiments": asset_sentiments,
                    "manipulation_detected": manipulation_check,
                    "correlation_with_returns": await self.performance_analyzer.get_sentiment_correlation(
                        portfolio_id=params.portfolio_id,
                        days=params.timeframe_days
                    ),
                    "sentiment_driven_risk": self._calculate_sentiment_risk(
                        asset_sentiments,
                        manipulation_check,
                        risk_assessment
                    )
                }
            
            return {
                "portfolio_id": params.portfolio_id,
                "timeframe_days": params.timeframe_days,
                "risk_metrics": risk_assessment,
                "sentiment_impact": sentiment_impact,
                "risk_summary": {
                    "overall_risk_score": risk_assessment.get("risk_score", 50),
                    "volatility": risk_assessment.get("volatility", 0),
                    "max_drawdown": risk_assessment.get("max_drawdown", 0),
                    "correlation_risk": risk_assessment.get("correlation_risk", 0),
                    "sentiment_risk_modifier": sentiment_impact.get("sentiment_driven_risk", {}).get("modifier", 0)
                        if params.include_sentiment_impact else 0
                },
                "recommendations": self._generate_risk_recommendations(
                    risk_assessment,
                    sentiment_impact if params.include_sentiment_impact else {}
                )
            }
        except Exception as e:
            logger.error(f"Error assessing risk: {str(e)}")
            return {
                "error": str(e),
                "message": "Error assessing risk"
            }
    
    @create_action(
        name="find-yield",
        description="Find optimized yield opportunities with sentiment considerations",
        schema=FindYieldParams
    )
    async def find_yield(self, params: FindYieldParams) -> Dict[str, Any]:
        """
        Find yield opportunities with sentiment context
        
        Identifies yield opportunities and filters them based on sentiment data,
        focusing on statistical yield calculations as recommended by Rose Heart.
        """
        try:
            # Get portfolio data
            portfolio = await self.db_manager.get_portfolio(params.portfolio_id)
            
            # Get yield opportunities from Yield Optimizer (purely statistical)
            opportunities = await self.yield_optimizer.find_opportunities(params.portfolio_id)
            
            # Filter by minimum APY
            filtered_opportunities = [
                opp for opp in opportunities 
                if opp.get("apy", 0) >= params.min_apy
            ]
            
            # Filter by risk tolerance
            risk_filtered = self._filter_by_risk_tolerance(
                filtered_opportunities,
                params.risk_tolerance
            )
            
            # Apply sentiment filter if requested
            final_opportunities = risk_filtered
            if params.include_sentiment_filter:
                # Get sentiment for relevant assets
                asset_symbols = list(set([opp["asset"] for opp in risk_filtered]))
                sentiments = await self.intelligence_engine.get_asset_sentiments(asset_symbols)
                
                # Filter opportunities based on sentiment
                final_opportunities = self._filter_by_sentiment(
                    risk_filtered,
                    sentiments
                )
            
            # Get optimal allocation suggestion
            optimal_allocation = await self.yield_optimizer._calculate_optimal_allocation(
                final_opportunities,
                portfolio
            )
            
            return {
                "portfolio_id": params.portfolio_id,
                "risk_tolerance": params.risk_tolerance,
                "min_apy": params.min_apy,
                "opportunities_found": len(final_opportunities),
                "opportunities": final_opportunities,
                "optimal_allocation": optimal_allocation,
                "estimated_portfolio_yield": self._calculate_portfolio_yield(
                    portfolio,
                    optimal_allocation
                ),
                "recommendations": self._generate_yield_recommendations(
                    final_opportunities,
                    portfolio
                )
            }
        except Exception as e:
            logger.error(f"Error finding yield opportunities: {str(e)}")
            return {
                "error": str(e),
                "message": "Error finding yield opportunities"
            }
    
    @create_action(
        name="simulate-rebalance",
        description="Simulate portfolio rebalance with custom allocations",
        schema=SimulateRebalanceParams
    )
    async def simulate_rebalance(self, params: SimulateRebalanceParams) -> Dict[str, Any]:
        """
        Simulate rebalancing with predicted outcomes
        
        Projects portfolio performance based on statistical models and sentiment data,
        without executing any trades.
        """
        try:
            # Get portfolio data
            portfolio = await self.db_manager.get_portfolio(params.portfolio_id)
            
            # Calculate rebalancing costs
            rebalancing_costs = await self.strategy_engine.calculate_rebalancing_costs(portfolio)
            
            # Get statistical projections
            statistical_projection = await self.risk_manager.project_portfolio_performance(
                portfolio_id=params.portfolio_id,
                target_allocations=params.target_allocations,
                days=params.time_horizon_days
            )
            
            # Get sentiment-enhanced projections
            sentiment_projection = await self.intelligence_engine.project_with_sentiment(
                portfolio_id=params.portfolio_id,
                target_allocations=params.target_allocations,
                days=params.time_horizon_days
            )
            
            # Calculate expected value after rebalancing
            combined_projection = self._combine_projections(
                statistical_projection,
                sentiment_projection
            )
            
            # Calculate trades required
            required_trades = await self.strategy_engine._calculate_required_trades(
                portfolio,
                params.target_allocations
            )
            
            return {
                "portfolio_id": params.portfolio_id,
                "current_allocations": {
                    asset["symbol"]: asset["percentage"] / 100 
                    for asset in portfolio.get("assets", [])
                },
                "target_allocations": params.target_allocations,
                "time_horizon_days": params.time_horizon_days,
                "rebalancing_costs": rebalancing_costs,
                "required_trades": required_trades,
                "projections": {
                    "statistical": statistical_projection,
                    "sentiment_enhanced": sentiment_projection,
                    "combined": combined_projection
                },
                "expected_return": combined_projection.get("expected_return", 0),
                "expected_risk": combined_projection.get("expected_risk", 0),
                "expected_sharpe": combined_projection.get("expected_sharpe", 0),
                "recommendations": self._generate_simulation_recommendations(
                    portfolio,
                    params.target_allocations,
                    combined_projection,
                    required_trades,
                    rebalancing_costs
                )
            }
        except Exception as e:
            logger.error(f"Error simulating rebalance: {str(e)}")
            return {
                "error": str(e),
                "message": "Error simulating rebalance"
            }
    
    def _generate_insights(self, analysis, stats, performance) -> List[str]:
        """Generate insights based on analysis, stats and performance data"""
        insights = []
        
        # Add insights based on available data
        if analysis.get("rebalance_recommended", False):
            insights.append(f"Rebalancing recommended: {analysis.get('reason', '')}")
        else:
            insights.append(f"No rebalancing needed: {analysis.get('reason', '')}")
            
        if "risk_level" in stats:
            insights.append(f"Portfolio risk level: {stats['risk_level']}")
            
        if "sentiment_accuracy" in performance:
            accuracy = performance["sentiment_accuracy"]
            insights.append(f"Sentiment signals have been {accuracy:.1%} accurate recently")
            
        if "manipulation_detected" in analysis and analysis["manipulation_detected"]:
            insights.append("Warning: Potential market manipulation detected")
            
        return insights
    
    def _calculate_sentiment_risk(self, sentiments, manipulation, risk_assessment) -> Dict[str, Any]:
        """Calculate risk modifier based on sentiment and manipulation detection"""
        # Start with neutral modifier
        modifier = 0
        reasons = []
        
        # Check for extreme sentiment
        for asset, sentiment in sentiments.items():
            if sentiment.get("sentiment") == "extreme_fear":
                modifier += 0.05
                reasons.append(f"Extreme fear detected for {asset}")
            elif sentiment.get("sentiment") == "extreme_greed":
                modifier += 0.05
                reasons.append(f"Extreme greed detected for {asset}")
                
        # Check for manipulation
        for asset, detected in manipulation.items():
            if detected:
                modifier += 0.1
                reasons.append(f"Potential manipulation detected for {asset}")
                
        return {
            "modifier": modifier,
            "adjusted_risk_score": min(100, risk_assessment.get("risk_score", 50) + modifier * 100),
            "reasons": reasons
        }
    
    def _generate_risk_recommendations(self, risk_assessment, sentiment_impact) -> List[str]:
        """Generate risk-related recommendations"""
        recommendations = []
        
        # Add recommendations based on risk metrics
        risk_score = risk_assessment.get("risk_score", 0)
        
        if risk_score > 80:
            recommendations.append("Consider reducing exposure to high-volatility assets")
        elif risk_score < 20:
            recommendations.append("Portfolio may be too conservative - consider adding growth assets")
            
        # Add sentiment-based recommendations
        if sentiment_impact:
            for asset, sentiment in sentiment_impact.get("asset_sentiments", {}).items():
                if sentiment.get("sentiment") == "extreme_fear" and sentiment.get("confidence", 0) > 0.7:
                    recommendations.append(f"High confidence fear signal for {asset} - consider defensive positioning")
                    
            # Manipulation warning
            if any(sentiment_impact.get("manipulation_detected", {}).values()):
                recommendations.append("Manipulation detected - exercise caution with recent price movements")
                
        return recommendations
    
    def _filter_by_risk_tolerance(self, opportunities, risk_tolerance) -> List[Dict[str, Any]]:
        """Filter yield opportunities by risk tolerance"""
        risk_mapping = {
            "conservative": 0.3,
            "moderate": 0.6,
            "aggressive": 1.0
        }
        
        max_risk = risk_mapping[risk_tolerance]
        
        return [
            opp for opp in opportunities
            if opp.get("risk_score", 0) / 100 <= max_risk
        ]
    
    def _filter_by_sentiment(self, opportunities, sentiments) -> List[Dict[str, Any]]:
        """Filter yield opportunities based on sentiment analysis"""
        filtered = []
        
        for opp in opportunities:
            asset = opp.get("asset")
            sentiment = sentiments.get(asset, {})
            
            # Skip opportunities with extreme fear and high confidence
            if (sentiment.get("sentiment") == "extreme_fear" and 
                sentiment.get("confidence", 0) > 0.8):
                continue
                
            # Skip opportunities where manipulation is likely
            if sentiment.get("manipulation_probability", 0) > 0.7:
                continue
                
            filtered.append(opp)
            
        return filtered
    
    def _calculate_portfolio_yield(self, portfolio, allocation) -> float:
        """Calculate expected portfolio yield based on allocation"""
        total_yield = 0
        total_allocated = 0
        
        for asset, alloc in allocation.items():
            apy = alloc.get("apy", 0)
            value = alloc.get("value", 0)
            
            total_yield += apy * value
            total_allocated += value
            
        if total_allocated > 0:
            return total_yield / total_allocated
        return 0
    
    def _generate_yield_recommendations(self, opportunities, portfolio) -> List[str]:
        """Generate yield-related recommendations"""
        recommendations = []
        
        if not opportunities:
            recommendations.append("No suitable yield opportunities found with current parameters")
            return recommendations
            
        # Group by protocol
        protocols = {}
        for opp in opportunities:
            protocol = opp.get("protocol", "unknown")
            if protocol not in protocols:
                protocols[protocol] = []
            protocols[protocol].append(opp)
            
        # Add protocol-specific recommendations
        for protocol, opps in protocols.items():
            if len(opps) > 1:
                recommendations.append(f"Consider {protocol} for multiple assets ({', '.join([o['asset'] for o in opps])})")
            else:
                recommendations.append(f"Consider {protocol} for {opps[0]['asset']} with {opps[0]['apy']:.2%} APY")
                
        return recommendations
    
    def _combine_projections(self, statistical, sentiment) -> Dict[str, Any]:
        """Combine statistical and sentiment-based projections with equal weights"""
        # Use equal weights as recommended by Rose Heart
        weights = {
            "statistical": 0.5,
            "sentiment": 0.5
        }
        
        combined = {}
        
        # Combine the key metrics
        for key in ["expected_return", "expected_risk", "expected_sharpe"]:
            if key in statistical and key in sentiment:
                combined[key] = (
                    statistical[key] * weights["statistical"] +
                    sentiment[key] * weights["sentiment"]
                )
        
        # Add confidence score
        combined["confidence"] = sentiment.get("confidence", 0.5)
        
        # Add asset-specific projections
        combined["assets"] = {}
        for asset in set(list(statistical.get("assets", {}).keys()) + list(sentiment.get("assets", {}).keys())):
            combined["assets"][asset] = {}
            
            # Combine asset metrics
            for key in ["expected_return", "expected_risk"]:
                stat_value = statistical.get("assets", {}).get(asset, {}).get(key, 0)
                sent_value = sentiment.get("assets", {}).get(asset, {}).get(key, 0)
                
                combined["assets"][asset][key] = (
                    stat_value * weights["statistical"] +
                    sent_value * weights["sentiment"]
                )
        
        return combined
    
    def _generate_simulation_recommendations(self, portfolio, target, projection, trades, costs) -> List[str]:
        """Generate recommendations based on simulation results"""
        recommendations = []
        
        # Check if rebalancing is cost-effective
        current_value = portfolio.get("total_value", 0)
        expected_return = projection.get("expected_return", 0) * current_value
        total_cost = costs.get("total_cost", 0)
        
        if expected_return <= total_cost * 2:  # Rose Heart's 2x threshold
            recommendations.append("Rebalancing costs may exceed potential benefits - consider delaying")
        else:
            recommendations.append(f"Expected benefit exceeds costs by {expected_return/total_cost:.1f}x")
            
        # Asset-specific recommendations
        for trade in trades:
            symbol = trade.get("symbol")
            action = trade.get("action")
            
            if symbol in projection.get("assets", {}):
                asset_projection = projection["assets"][symbol]
                
                if action == "buy" and asset_projection.get("expected_return", 0) < 0:
                    recommendations.append(f"Caution: Buying {symbol} despite negative expected return")
                elif action == "sell" and asset_projection.get("expected_return", 0) > 0.05:  # 5%
                    recommendations.append(f"Caution: Selling {symbol} despite positive expected return")
        
        return recommendations

def portfolio_action_provider(
    wallet_provider: EvmWalletProvider,
    intelligence_engine: IntelligenceEngine, 
    strategy_engine: StrategyEngine,
    risk_manager: RiskManager,
    yield_optimizer: YieldOptimizer,
    performance_analyzer: PerformanceAnalyzer,
    db_manager,
    config: Dict[str, Any]
) -> PortfolioActionProvider:
    """Create a PortfolioActionProvider instance"""
    return PortfolioActionProvider(
        wallet_provider=wallet_provider,
        intelligence_engine=intelligence_engine,
        strategy_engine=strategy_engine,
        risk_manager=risk_manager,
        yield_optimizer=yield_optimizer,
        performance_analyzer=performance_analyzer,
        db_manager=db_manager,
        config=config
    )
