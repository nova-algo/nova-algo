"""
MarketActionProvider

Provides actions for market analysis and predictions, implementing the AgentKit action provider pattern.
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Type, Union
from pydantic import BaseModel, Field, validator
from decimal import Decimal


from coinbase_agentkit.action_providers.action_decorator import create_action
from coinbase_agentkit.action_providers.action_provider import ActionProvider
from coinbase_agentkit.network import Network
from coinbase_agentkit.wallet_providers import EvmWalletProvider

from rebalancr.intelligence.allora.client import AlloraClient
from rebalancr.intelligence.market_analysis import MarketAnalyzer
from rebalancr.intelligence.market_data import MarketDataAnalyzer
from rebalancr.intelligence.market_conditions import MarketConditionClassifier

logger = logging.getLogger(__name__)

# Supported assets for market predictions
SUPPORTED_ASSETS = ["BTC", "ETH"]
TOPIC_IDS = {"BTC": 14, "ETH": 13}

class MarketPredictionParams(BaseModel):
    """Parameters for market prediction"""
    asset: str = Field(..., description="Asset symbol (e.g., BTC, ETH)")
    include_sentiment: bool = Field(True, description="Include sentiment analysis")
    include_technical: bool = Field(True, description="Include technical indicators")
    time_horizon: str = Field("short", description="Time horizon for prediction (short, medium, long)")
    
    @validator('asset')
    def validate_asset(cls, v):
        """Validate that asset is supported"""
        if v.upper() not in SUPPORTED_ASSETS:
            raise ValueError(f"Asset must be one of {SUPPORTED_ASSETS}")
        return v.upper()
    
    @validator('time_horizon')
    def validate_time_horizon(cls, v):
        """Validate time horizon"""
        if v not in ["short", "medium", "long"]:
            raise ValueError('Time horizon must be "short", "medium", or "long"')
        return v

class MarketTrendParams(BaseModel):
    """Parameters for market trend analysis"""
    asset: str = Field(..., description="Asset symbol (e.g., BTC, ETH)")
    days: int = Field(30, ge=1, le=365, description="Number of days for trend analysis")
    
    @validator('asset')
    def validate_asset(cls, v):
        if v.upper() not in SUPPORTED_ASSETS:
            raise ValueError(f"Asset must be one of {SUPPORTED_ASSETS}")
        return v.upper()
    
    @validator('days')
    def validate_days(cls, v):
        if v < 1 or v > 365:
            raise ValueError("Days must be between 1 and 365")
        return v

class MarketVolatilityParams(BaseModel):
    """Parameters for market volatility analysis"""
    asset: str = Field(..., description="Asset symbol (e.g., BTC, ETH)")
    days: int = Field(14, ge=1, le=90, description="Number of days for volatility calculation")
    
    @validator('asset')
    def validate_asset(cls, v):
        if v.upper() not in SUPPORTED_ASSETS:
            raise ValueError(f"Asset must be one of {SUPPORTED_ASSETS}")
        return v.upper()

class MarketActionProvider(ActionProvider):
    """
    Provides market analysis actions
    
    Implements Rose Heart's dual-system approach:
    - AI for sentiment analysis (via Allora)
    - Statistical methods for numerical analysis (via MarketAnalyzer)
    """
    
    def __init__(
        self,
        allora_client: AlloraClient,
        market_analyzer: MarketAnalyzer,
        market_data_service: Optional[MarketDataAnalyzer] = None,
        market_condition_classifier: Optional[MarketConditionClassifier] = None,
        config: Dict[str, Any] = None
    ):
        super().__init__(
            name="market-action", 
            action_providers=[]  # Empty list since actions are defined using decorators
        )
        self.allora_client = allora_client
        self.market_analyzer = market_analyzer
        self.market_data_service = market_data_service
        self.market_condition_classifier = market_condition_classifier
        self.config = config or {}
    
    @create_action(
        name="predict-market",
        description="Get market prediction for an asset combining sentiment and statistical analysis",
        schema=MarketPredictionParams
    )
    async def predict_market(self, params: MarketPredictionParams) -> Dict[str, Any]:
        """
        Get market prediction for an asset combining sentiment and statistical analysis
        
        Implements Rose Heart's dual-system approach:
        - AI sentiment analysis from Allora
        - Statistical metrics from traditional methods
        """
        try:
            asset = params.asset
            topic_id = TOPIC_IDS.get(asset)
            
            if not topic_id:
                return {"error": f"Unsupported asset: {asset}. Currently supporting {SUPPORTED_ASSETS}"}
            
            # Get Allora prediction (sentiment)
            prediction = await self.allora_client.get_prediction(topic_id)
            
            # Get statistical analysis
            historical_data = await self._get_historical_data(asset)
            metrics = self.market_analyzer.calculate_asset_metrics(historical_data)
            
            # Get market condition if classifier is available
            market_condition = None
            if self.market_condition_classifier and metrics:
                market_condition = self.market_condition_classifier.classify(metrics, prediction)
            
            # Add technical indicators if requested
            technical_indicators = "Mixed signals"
            if params.include_technical and self.market_data_service:
                trend_analysis = await self.market_data_service.analyze_market_trend(asset)
                technical_indicators = {
                    "trend": trend_analysis.get("trend", "neutral"),
                    "ma5": trend_analysis.get("MA5"),
                    "ma20": trend_analysis.get("MA20")
                }
            
            # Combine insights
            response = {
                "message": f"Analysis for {asset}:",
                "prediction": {
                    "sentiment": prediction.get("sentiment", "neutral"),
                    "direction": prediction.get("direction", "sideways"),
                    "confidence": prediction.get("confidence", 0.5),
                },
                "statistics": {
                    "volatility": metrics.get("volatility"),
                    "current_vs_median": metrics.get("below_median_frequency"),
                    "technical_indicators": technical_indicators
                },
                "market_condition": market_condition,
                "time_horizon": params.time_horizon,
                "recommendation": self._generate_recommendation(prediction, metrics, params.time_horizon)
            }
            
            return response
        except Exception as e:
            logger.error(f"Error getting market prediction: {str(e)}")
            return {"error": f"Failed to get prediction: {str(e)}"}
    
    @create_action(
        name="analyze-trend",
        description="Analyze market trend for an asset over a specified time period",
        schema=MarketTrendParams
    )
    async def analyze_trend(self, params: MarketTrendParams) -> Dict[str, Any]:
        """Analyze market trend for an asset"""
        try:
            asset = params.asset
            days = params.days
            
            # Get trend analysis from market data service
            if self.market_data_service:
                trend_analysis = await self.market_data_service.analyze_market_trend(asset, days)
                return trend_analysis
            
            # Fallback using historical data and market analyzer
            historical_data = await self._get_historical_data(asset, days)
            trend = self._analyze_trend_from_data(historical_data)
            
            return {
                "asset": asset,
                "days": days,
                "trend": trend.get("trend", "neutral"),
                "confidence": trend.get("confidence", 50),
                "supporting_metrics": trend.get("metrics", {})
            }
        except Exception as e:
            logger.error(f"Error analyzing trend: {str(e)}")
            return {"error": f"Failed to analyze trend: {str(e)}"}
    
    @create_action(
        name="calculate-volatility",
        description="Calculate volatility and risk level for an asset",
        schema=MarketVolatilityParams
    )
    async def calculate_volatility(self, params: MarketVolatilityParams) -> Dict[str, Any]:
        """Calculate volatility for an asset"""
        try:
            asset = params.asset
            days = params.days
            
            # Use market data service if available
            if self.market_data_service:
                volatility = await self.market_data_service.calculate_volatility(asset, days)
                return volatility
            
            # Fallback using historical data
            historical_data = await self._get_historical_data(asset, days)
            metrics = self.market_analyzer.calculate_asset_metrics(historical_data)
            
            return {
                "asset": asset,
                "days": days,
                "volatility": metrics.get("volatility", 0),
                "risk_level": self._get_risk_level(metrics.get("volatility", 0))
            }
        except Exception as e:
            logger.error(f"Error calculating volatility: {str(e)}")
            return {"error": f"Failed to calculate volatility: {str(e)}"}
    
    # Helper methods
    
    async def _get_historical_data(self, asset: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get historical data for statistical analysis"""
        # If market data service is available, use it
        if self.market_data_service:
            return await self.market_data_service.get_historical_prices(asset, days)
        
        # Otherwise return simulated data
        return [{"price": 60000, "timestamp": "2023-01-01"}]
    
    def _analyze_trend_from_data(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trend from historical data"""
        if not historical_data or len(historical_data) < 2:
            return {"trend": "unknown", "confidence": 0}
        
        # Simple trend analysis based on first and last price
        first_price = historical_data[0]["price"]
        last_price = historical_data[-1]["price"]
        
        change_pct = (last_price - first_price) / first_price * 100
        
        if change_pct > 5:
            trend = "bullish"
            confidence = min(100, abs(change_pct) * 2)
        elif change_pct < -5:
            trend = "bearish"
            confidence = min(100, abs(change_pct) * 2)
        else:
            trend = "neutral"
            confidence = 50
            
        return {
            "trend": trend,
            "confidence": confidence,
            "metrics": {
                "price_change_pct": change_pct,
                "start_price": first_price,
                "end_price": last_price
            }
        }
    
    def _get_risk_level(self, volatility: float) -> str:
        """Get risk level based on volatility"""
        if volatility < 0.3:
            return "low"
        elif volatility < 0.6:
            return "medium"
        else:
            return "high"
    
    def _generate_recommendation(self, prediction: Dict[str, Any], metrics: Dict[str, Any], time_horizon: str = "short") -> Dict[str, Any]:
        """Generate a recommendation combining AI sentiment and statistical metrics"""
        recommendation = "HOLD"
        confidence = 0
        
        # Use AI prediction for sentiment-based signals
        sentiment_score = 0
        if prediction.get("sentiment") == "bullish":
            sentiment_score = 1
        elif prediction.get("sentiment") == "bearish":
            sentiment_score = -1
            
        # Use statistical metrics for numerical analysis
        stats_score = 0
        if metrics.get("below_median_frequency", 0.5) < 0.4:
            # Price is frequently above median, potential uptrend
            stats_score += 0.5
        elif metrics.get("below_median_frequency", 0.5) > 0.6:
            # Price is frequently below median, potential downtrend
            stats_score -= 0.5
            
        # Volatility check - lower score for high volatility
        if metrics.get("volatility", 0.5) > 0.8:
            stats_score *= 0.7  # Reduce confidence for high volatility
            
        # Time horizon adjustments
        weight_adjustments = {
            "short": {"sentiment": 0.6, "stats": 0.4},   # Short-term: more sentiment
            "medium": {"sentiment": 0.5, "stats": 0.5},  # Medium-term: balanced
            "long": {"sentiment": 0.3, "stats": 0.7}     # Long-term: more stats
        }
        
        weights = weight_adjustments.get(time_horizon, {"sentiment": 0.5, "stats": 0.5})
        
        # Combine scores with weights
        # Following Rose Heart's advice on weighting based on time horizon
        final_score = (sentiment_score * weights["sentiment"]) + (stats_score * weights["stats"])
        
        if final_score > 0.3:
            recommendation = "BUY"
            confidence = min(abs(final_score) * 100, 100)
        elif final_score < -0.3:
            recommendation = "SELL"
            confidence = min(abs(final_score) * 100, 100)
        else:
            recommendation = "HOLD"
            confidence = max(0, (1 - abs(final_score)) * 100)
            
        return {
            "action": recommendation,
            "confidence": confidence,
            "time_horizon": time_horizon,
            "reasoning": f"Combined AI sentiment ({sentiment_score}) and statistical signals ({stats_score}) with {time_horizon}-term weights"
        }

    def supports_network(self, network: Network) -> bool:
        """
        Check if the provider supports the given network
        
        Args:
            network: The network to check support for
            
        Returns:
            Boolean indicating whether the network is supported
        """
        # List of supported network IDs or names
        supported_networks = ["ethereum", "base-mainnet", "base-sepolia", "arbitrum-one"]
        
        # Check if the network is supported
        if isinstance(network, str):
            return network in supported_networks
        elif hasattr(network, 'id') or hasattr(network, 'name'):
            # If network is an object with id or name attribute
            network_id = getattr(network, 'id', getattr(network, 'name', None))
            return network_id in supported_networks
        
        return False

def market_action_provider(
    allora_client: AlloraClient,
    market_analyzer: MarketAnalyzer,
    market_data_service: Optional[MarketDataAnalyzer] = None,
    market_condition_classifier: Optional[MarketConditionClassifier] = None,
    config: Dict[str, Any] = None
) -> MarketActionProvider:
    """Create a Market Action Provider instance"""
    return MarketActionProvider(
        allora_client=allora_client,
        market_analyzer=market_analyzer,
        market_data_service=market_data_service,
        market_condition_classifier=market_condition_classifier,
        config=config
    )
