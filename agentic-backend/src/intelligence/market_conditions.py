"""
Market Condition Classifier

Detects market conditions (normal, volatile, bull, bear) based on statistical metrics
and sentiment analysis. This is used to adapt weights in the decision-making process.
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class MarketCondition(str, Enum):
    """Possible market conditions"""
    NORMAL = "normal"
    VOLATILE = "volatile"
    BULL = "bull"
    BEAR = "bear"

class MarketConditionClassifier:
    """
    Classifies market conditions based on statistical metrics and sentiment
    
    This implements a statistical approach to market condition classification,
    following Rose Heart's recommendation to use traditional statistics for
    numerical operations.
    """
    
    def __init__(self, config=None):
        """Initialize classifier with configuration"""
        self.config = config or {}
        
        # Thresholds for classification
        self.volatility_threshold = self.config.get("volatility_threshold", 0.3)
        self.bull_threshold = self.config.get("bull_threshold", 0.1)  # 10% gain in short period
        self.bear_threshold = self.config.get("bear_threshold", -0.1)  # 10% loss in short period
        
        # Fear/greed thresholds from sentiment
        self.fear_threshold = self.config.get("fear_threshold", 0.3)
        self.greed_threshold = self.config.get("greed_threshold", 0.7)
        
        # Market history cache
        self.market_history = {}
        
    def classify(self, metrics: Dict[str, Any], sentiment: Optional[Dict[str, Any]] = None) -> MarketCondition:
        """
        Classify market condition based on metrics and optional sentiment
        
        Args:
            metrics: Dictionary with statistical metrics (volatility, returns, etc.)
            sentiment: Optional dictionary with sentiment metrics (fear/greed score)
            
        Returns:
            MarketCondition value
        """
        # Check for high volatility first
        if self._is_volatile(metrics):
            return MarketCondition.VOLATILE
            
        # Check for bull/bear market
        if self._is_bull_market(metrics, sentiment):
            return MarketCondition.BULL
            
        if self._is_bear_market(metrics, sentiment):
            return MarketCondition.BEAR
            
        # Default to normal market
        return MarketCondition.NORMAL
    
    def classify_for_asset(self, asset: str, metrics: Dict[str, Any], sentiment: Optional[Dict[str, Any]] = None) -> MarketCondition:
        """
        Classify market condition for a specific asset
        
        Args:
            asset: Asset symbol (e.g., "BTC")
            metrics: Dictionary with statistical metrics
            sentiment: Optional dictionary with sentiment metrics
            
        Returns:
            MarketCondition value
        """
        # Update market history for the asset
        self._update_market_history(asset, metrics)
        
        # Get asset-specific volatility if available
        if asset in self.market_history:
            history = self.market_history[asset]
            if len(history) > 10:  # Need sufficient history
                # Calculate recent volatility
                recent_returns = np.diff(np.log(history[-10:]))
                recent_volatility = np.std(recent_returns) * np.sqrt(252)  # Annualized
                
                # Override volatility in metrics
                metrics["volatility"] = recent_volatility
        
        # Use standard classification
        return self.classify(metrics, sentiment)
        
    def _is_volatile(self, metrics: Dict[str, Any]) -> bool:
        """Check if market is volatile based on metrics"""
        volatility = metrics.get("volatility", 0)
        return volatility > self.volatility_threshold
        
    def _is_bull_market(self, metrics: Dict[str, Any], sentiment: Optional[Dict[str, Any]] = None) -> bool:
        """Check if market is in bull condition"""
        # Check price trend
        price_change = metrics.get("recent_return", 0)
        
        # Check sentiment if available
        sentiment_bullish = False
        if sentiment:
            fear_greed = sentiment.get("fear_greed_index", 50)
            sentiment_bullish = fear_greed > self.greed_threshold * 100  # Convert to 0-100 scale
            
        # Consider both statistical and sentiment signals
        # Pure statistical approach as Rose Heart advised
        statistical_bullish = price_change > self.bull_threshold
        
        # Sentiment can confirm but not override statistical signal
        return statistical_bullish and (sentiment is None or sentiment_bullish)
        
    def _is_bear_market(self, metrics: Dict[str, Any], sentiment: Optional[Dict[str, Any]] = None) -> bool:
        """Check if market is in bear condition"""
        # Check price trend
        price_change = metrics.get("recent_return", 0)
        
        # Check sentiment if available
        sentiment_bearish = False
        if sentiment:
            fear_greed = sentiment.get("fear_greed_index", 50)
            sentiment_bearish = fear_greed < self.fear_threshold * 100  # Convert to 0-100 scale
            
        # Consider both statistical and sentiment signals
        # Pure statistical approach as Rose Heart advised
        statistical_bearish = price_change < self.bear_threshold
        
        # Sentiment can confirm but not override statistical signal
        return statistical_bearish and (sentiment is None or sentiment_bearish)
        
    def _update_market_history(self, asset: str, metrics: Dict[str, Any]) -> None:
        """Update market history for an asset"""
        price = metrics.get("price", None)
        if price is None:
            return
            
        if asset not in self.market_history:
            self.market_history[asset] = []
            
        # Add price to history
        self.market_history[asset].append(price)
        
        # Keep limited history (latest 100 points)
        self.market_history[asset] = self.market_history[asset][-100:]
    
    def get_all_conditions(self, metrics: Dict[str, Any], sentiment: Optional[Dict[str, Any]] = None) -> Dict[str, bool]:
        """
        Get all possible market conditions with boolean indicators
        
        This is useful for debugging or for more granular condition handling
        
        Args:
            metrics: Dictionary with statistical metrics
            sentiment: Optional dictionary with sentiment metrics
            
        Returns:
            Dictionary with condition name and boolean value
        """
        return {
            MarketCondition.VOLATILE.value: self._is_volatile(metrics),
            MarketCondition.BULL.value: self._is_bull_market(metrics, sentiment),
            MarketCondition.BEAR.value: self._is_bear_market(metrics, sentiment),
            MarketCondition.NORMAL.value: not any([
                self._is_volatile(metrics),
                self._is_bull_market(metrics, sentiment),
                self._is_bear_market(metrics, sentiment)
            ])
        }
        
    def detect_market_transition(
        self, 
        asset: str,
        historical_metrics: List[Dict[str, Any]],
        historical_sentiment: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Tuple[MarketCondition, MarketCondition]]:
        """
        Detect transitions between market conditions
        
        Args:
            asset: Asset symbol
            historical_metrics: List of metrics dictionaries over time
            historical_sentiment: Optional list of sentiment dictionaries
            
        Returns:
            Tuple of (old_condition, new_condition) or None if no transition
        """
        if len(historical_metrics) < 2:
            return None
            
        # Get current condition
        current_metrics = historical_metrics[-1]
        current_sentiment = historical_sentiment[-1] if historical_sentiment else None
        current_condition = self.classify_for_asset(asset, current_metrics, current_sentiment)
        
        # Get previous condition
        prev_metrics = historical_metrics[-2]
        prev_sentiment = historical_sentiment[-2] if historical_sentiment else None
        prev_condition = self.classify_for_asset(asset, prev_metrics, prev_sentiment)
        
        # Check for transition
        if current_condition != prev_condition:
            return (prev_condition, current_condition)
            
        return None 