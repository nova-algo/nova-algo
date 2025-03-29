import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class MarketAnalyzer:
    """
    Statistical analysis for trading decisions.
    
    Following Rose Heart's advice, this class implements traditional
    statistical methods for numerical analysis, separate from AI.
    """
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        
    async def analyze_asset(self, asset: str, history_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate statistical metrics for an asset (Rose Heart's advice)
        
        Args:
            asset: Asset symbol (e.g., "BTC")
            history_data: DataFrame with historical price data
            
        Returns:
            Dictionary with statistical analysis results
        """
        try:
            # Calculate asset-specific statistics as Rose Heart suggested
            median_price = history_data["price"].median()
            below_median_freq = (history_data["price"] < median_price).mean()
            
            # Volatility calculation
            returns = history_data["price"].pct_change().dropna()
            volatility = returns.std() * np.sqrt(365)  # Annualized
            
            # Trend analysis
            price_20d_avg = history_data["price"].rolling(window=20).mean().iloc[-1]
            price_50d_avg = history_data["price"].rolling(window=50).mean().iloc[-1]
            trend = "uptrend" if price_20d_avg > price_50d_avg else "downtrend"
            
            # Calculate relative strength
            market_returns = history_data.get("market_returns", pd.Series([0] * len(returns)))
            if len(returns) > 0 and len(market_returns) > 0:
                beta = returns.cov(market_returns) / market_returns.var() if market_returns.var() > 0 else 1.0
            else:
                beta = 1.0
                
            return {
                "asset": asset,
                "median_price": float(median_price),
                "below_median_frequency": float(below_median_freq),
                "volatility": float(volatility),
                "trend": trend,
                "beta": float(beta),
                # Rose Heart advised to use this for rebalancing decisions
                "statistical_signal": "reduce" if below_median_freq > 0.6 else 
                                      "increase" if below_median_freq < 0.4 else 
                                      "maintain"
            }
        except Exception as e:
            logger.error(f"Error analyzing asset {asset}: {str(e)}")
            return {
                "asset": asset,
                "error": str(e),
                "statistical_signal": "maintain"  # Default to no change on error
            }

    def analyze_rebalance_opportunity(
        self, 
        portfolio: Dict[str, float], 
        target_weights: Dict[str, float],
        current_prices: Dict[str, float],
        fee_rate: float = 0.001
    ) -> Dict[str, Any]:
        """
        Analyze whether rebalancing is profitable based on statistical methods
        
        Args:
            portfolio: Current portfolio holdings {asset: amount}
            target_weights: Target allocation {asset: weight}
            current_prices: Current asset prices {asset: price}
            fee_rate: Trading fee rate
            
        Returns:
            Analysis results and recommendation
        """
        # Calculate current portfolio value and weights
        portfolio_value = sum(portfolio[asset] * current_prices[asset] 
                             for asset in portfolio)
        current_weights = {
            asset: (portfolio[asset] * current_prices[asset]) / portfolio_value
            for asset in portfolio
        }
        
        # Calculate required trades to achieve target weights
        trades = {}
        estimated_fees = 0
        
        for asset in target_weights:
            target_value = portfolio_value * target_weights[asset]
            current_value = portfolio[asset] * current_prices[asset]
            value_diff = target_value - current_value
            
            if abs(value_diff) > 0:
                amount_diff = value_diff / current_prices[asset]
                trades[asset] = amount_diff
                # Calculate fees for this trade
                estimated_fees += abs(value_diff) * fee_rate
        
        # Expected portfolio improvement
        deviation_before = sum(
            abs(current_weights.get(asset, 0) - target_weights.get(asset, 0))
            for asset in set(current_weights) | set(target_weights)
        )
        
        # Is rebalancing profitable after fees?
        is_profitable = (portfolio_value * 0.001 * deviation_before) > estimated_fees
        
        return {
            "current_weights": current_weights,
            "target_weights": target_weights,
            "deviation": deviation_before,
            "trades": trades,
            "estimated_fees": estimated_fees,
            "is_profitable": is_profitable,
            "recommendation": "rebalance" if is_profitable else "hold"
        }
        
    def calculate_asset_metrics(self, asset_data: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate statistical metrics for an asset
        
        Implements Rose Heart's recommendation for asset-specific parameters
        """
        # Calculate various statistical metrics
        median_price = asset_data["price"].median()
        below_median_freq = (asset_data["price"] < median_price).mean()
        volatility = asset_data["price"].pct_change().std() * np.sqrt(365)
        
        # Additional metrics as needed
        sharpe = None
        if "returns" in asset_data:
            mean_return = asset_data["returns"].mean() * 365
            return_volatility = asset_data["returns"].std() * np.sqrt(365)
            if return_volatility > 0:
                sharpe = mean_return / return_volatility
                
        return {
            "median_price": median_price,
            "below_median_frequency": below_median_freq,
            "volatility": volatility,
            "sharpe_ratio": sharpe
        }
