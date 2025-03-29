import asyncio
import logging
from typing import Dict, List, Any
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class RiskMonitor:
    """
    Monitors portfolio-specific risk metrics.
    
    Following Rose Heart's advice, this focuses on statistical 
    portfolio metrics rather than sentiment-based metrics.
    """
    
    def __init__(self, db_manager, config):
        self.db_manager = db_manager
        self.config = config
        self.portfolio_risks = {}
        
    async def start_monitoring(self, interval_seconds: int = 300):
        """Start continuous risk monitoring"""
        while True:
            try:
                # Get all active portfolios
                portfolios = await self.db_manager.get_active_portfolios()
                
                for portfolio in portfolios:
                    await self.update_portfolio_risk(portfolio["id"])
                
                logger.info(f"Updated risk metrics for {len(portfolios)} portfolios")
            except Exception as e:
                logger.error(f"Error updating risk metrics: {str(e)}")
            
            await asyncio.sleep(interval_seconds)
    
    async def update_portfolio_risk(self, portfolio_id: int):
        """Update risk metrics for a specific portfolio"""
        try:
            # Get portfolio data
            portfolio = await self.db_manager.get_portfolio(portfolio_id)
            assets = portfolio.get("assets", [])
            
            # Get current prices and historical data
            prices = {}
            historical_data = {}
            
            for asset in assets:
                symbol = asset["symbol"]
                price_data = await self.db_manager.get_asset_price_history(symbol)
                prices[symbol] = price_data["current_price"]
                historical_data[symbol] = pd.DataFrame(price_data["history"])
            
            # Calculate portfolio value
            total_value = sum(asset["amount"] * prices.get(asset["symbol"], 0) for asset in assets)
            
            # Calculate weights
            weights = {asset["symbol"]: (asset["amount"] * prices.get(asset["symbol"], 0)) / total_value 
                      for asset in assets if prices.get(asset["symbol"], 0) > 0}
            
            # Calculate portfolio metrics - purely statistical as Rose Heart advised
            portfolio_volatility = self._calculate_portfolio_volatility(weights, historical_data)
            max_drawdown = self._calculate_max_drawdown(weights, historical_data)
            value_at_risk = self._calculate_value_at_risk(weights, historical_data)
            
            # Check if any asset exceeds allocation limits
            allocation_warnings = []
            for symbol, weight in weights.items():
                if weight > self.config.MAX_ASSET_ALLOCATION:
                    allocation_warnings.append(f"{symbol} allocation ({weight:.1%}) exceeds maximum ({self.config.MAX_ASSET_ALLOCATION:.1%})")
            
            # Store risk metrics
            self.portfolio_risks[portfolio_id] = {
                "updated_at": pd.Timestamp.now().isoformat(),
                "total_value": total_value,
                "volatility": portfolio_volatility,
                "max_drawdown": max_drawdown,
                "value_at_risk_95": value_at_risk,
                "allocation_warnings": allocation_warnings,
                "risk_level": self._determine_risk_level(portfolio_volatility, max_drawdown),
                "rebalance_needed": len(allocation_warnings) > 0 or max_drawdown > self.config.MAX_DRAWDOWN_THRESHOLD
            }
            
            return self.portfolio_risks[portfolio_id]
        except Exception as e:
            logger.error(f"Error calculating portfolio risk for {portfolio_id}: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_portfolio_volatility(self, weights, historical_data):
        """Calculate portfolio volatility using statistical methods"""
        # Per Rose Heart's advice - use statistical method for numerical calculations
        returns = {}
        for symbol, data in historical_data.items():
            if "price" in data.columns and len(data) > 1:
                returns[symbol] = data["price"].pct_change().dropna()
        
        if not returns:
            return 0.0
        
        # Create returns DataFrame
        returns_df = pd.DataFrame(returns)
        
        # Handle missing data
        returns_df = returns_df.fillna(0)
        
        # Calculate covariance matrix
        cov_matrix = returns_df.cov()
        
        # Calculate portfolio volatility
        portfolio_variance = 0
        for symbol1, weight1 in weights.items():
            for symbol2, weight2 in weights.items():
                if symbol1 in cov_matrix.index and symbol2 in cov_matrix.columns:
                    portfolio_variance += weight1 * weight2 * cov_matrix.loc[symbol1, symbol2]
        
        return float(np.sqrt(portfolio_variance) * np.sqrt(365))  # Annualized
    
    def _calculate_max_drawdown(self, weights, historical_data):
        """Calculate maximum drawdown for portfolio"""
        # Simplified implementation
        return 0.15  # Placeholder
    
    def _calculate_value_at_risk(self, weights, historical_data):
        """Calculate 95% Value at Risk"""
        # Simplified implementation
        return 0.05  # Placeholder
    
    def _determine_risk_level(self, volatility, drawdown):
        """Determine portfolio risk level"""
        if volatility > 0.5 or drawdown > 0.3:
            return "high"
        elif volatility > 0.3 or drawdown > 0.2:
            return "medium"
        else:
            return "low"
    
    def get_portfolio_risk(self, portfolio_id: int) -> Dict[str, Any]:
        """Get current risk metrics for a portfolio"""
        return self.portfolio_risks.get(portfolio_id, {})
