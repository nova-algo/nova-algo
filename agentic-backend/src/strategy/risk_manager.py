import logging
from typing import Dict, List, Any
import numpy as np

logger = logging.getLogger(__name__)

class RiskManager:
    """
    Manages portfolio risk based on statistical metrics.
    
    Following Rose Heart's advice, this uses purely statistical
    methods for risk assessment and management.
    """
    
    def __init__(self, db_manager, config):
        self.db_manager = db_manager
        self.config = config
        
    async def assess_portfolio_risk(self, portfolio_id: int) -> Dict[str, Any]:
        """Assess portfolio risk using statistical methods"""
        try:
            # Get portfolio data
            portfolio = await self.db_manager.get_portfolio(portfolio_id)
            assets = portfolio.get("assets", [])
            
            # Calculate risk metrics
            concentration_risk = self._calculate_concentration_risk(assets)
            volatility_risk = self._calculate_volatility_risk(assets)
            correlation_risk = self._calculate_correlation_risk(assets)
            
            # Calculate overall risk score - purely statistical approach
            risk_score = (
                concentration_risk * 0.3 +
                volatility_risk * 0.5 +
                correlation_risk * 0.2
            )
            
            # Determine risk level
            risk_level = "low"
            if risk_score > 0.7:
                risk_level = "high"
            elif risk_score > 0.4:
                risk_level = "medium"
            
            # Generate risk warnings
            warnings = []
            
            if concentration_risk > 0.7:
                warnings.append("High concentration risk - portfolio too concentrated in few assets")
            
            if volatility_risk > 0.7:
                warnings.append("High volatility risk - consider reducing allocation to volatile assets")
            
            if correlation_risk > 0.7:
                warnings.append("High correlation risk - assets tend to move together")
            
            return {
                "portfolio_id": portfolio_id,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "concentration_risk": concentration_risk,
                "volatility_risk": volatility_risk,
                "correlation_risk": correlation_risk,
                "warnings": warnings
            }
        except Exception as e:
            logger.error(f"Error assessing portfolio risk: {str(e)}")
            return {
                "portfolio_id": portfolio_id,
                "error": str(e)
            }
    
    def _calculate_concentration_risk(self, assets: List[Dict[str, Any]]) -> float:
        """
        Calculate concentration risk using Herfindahl-Hirschman Index
        
        Pure statistical approach as Rose Heart advised
        """
        total_value = sum(asset.get("value", 0) for asset in assets)
        if total_value == 0:
            return 0
            
        weights = [asset.get("value", 0) / total_value for asset in assets]
        hhi = sum(w * w for w in weights)
        
        # Normalize to 0-1 range
        # HHI of 1 means complete concentration, 1/n means equal distribution
        n = len(assets)
        if n <= 1:
            return 1
            
        normalized_hhi = (hhi - (1/n)) / (1 - (1/n))
        return max(0, min(1, normalized_hhi))
    
    def _calculate_volatility_risk(self, assets: List[Dict[str, Any]]) -> float:
        """Calculate volatility risk based on asset historical volatility"""
        # Simplified implementation
        # In a real system, this would use historical volatility data
        
        # Map of asset types to estimated volatility
        volatility_map = {
            "BTC": 0.8,
            "ETH": 0.7,
            "SOL": 0.9,
            "ADA": 0.65,
            "USDC": 0.05,
            "USDT": 0.05,
            "DAI": 0.1
        }
        
        total_value = sum(asset.get("value", 0) for asset in assets)
        if total_value == 0:
            return 0
            
        weighted_volatility = sum(
            asset.get("value", 0) / total_value * volatility_map.get(asset.get("symbol", ""), 0.5)
            for asset in assets
        )
        
        return weighted_volatility
    
    def _calculate_correlation_risk(self, assets: List[Dict[str, Any]]) -> float:
        """Calculate correlation risk based on asset correlations"""
        # Simplified implementation
        # In a real system, this would calculate actual correlations
        
        # Count how many assets are in each category
        crypto_count = sum(1 for asset in assets if asset.get("symbol") in ["BTC", "ETH", "SOL", "ADA"])
        stablecoin_count = sum(1 for asset in assets if asset.get("symbol") in ["USDC", "USDT", "DAI"])
        
        total_assets = len(assets)
        if total_assets <= 1:
            return 0
            
        # High correlation if most assets are in the same category
        if crypto_count / total_assets > 0.8 or stablecoin_count / total_assets > 0.8:
            return 0.8
        elif crypto_count / total_assets > 0.6 or stablecoin_count / total_assets > 0.6:
            return 0.6
        else:
            return 0.3
    
    async def validate_rebalance_plan(self, portfolio_id: int, target_allocations: Dict[str, float]) -> Dict[str, Any]:
        """
        Validate a rebalancing plan against risk constraints
        
        Ensures the rebalancing respects risk limits (Rose Heart's clear thresholds)
        """
        try:
            # Get portfolio data
            portfolio = await self.db_manager.get_portfolio(portfolio_id)
            
            # Check concentration limits
            max_allocation = max(target_allocations.values())
            if max_allocation > self.config.MAX_ASSET_ALLOCATION:
                return {
                    "valid": False,
                    "reason": f"Maximum allocation of {max_allocation:.1%} exceeds limit of {self.config.MAX_ASSET_ALLOCATION:.1%}"
                }
            
            # Check minimum allocation
            min_allocation = min(target_allocations.values())
            if min_allocation < self.config.MIN_ASSET_ALLOCATION and len(target_allocations) > 5:
                return {
                    "valid": False,
                    "reason": f"Minimum allocation of {min_allocation:.1%} is below limit of {self.config.MIN_ASSET_ALLOCATION:.1%}"
                }
            
            # Check stablecoin allocation
            stablecoins = ["USDC", "USDT", "DAI"]
            stablecoin_allocation = sum(target_allocations.get(coin, 0) for coin in stablecoins)
            if stablecoin_allocation < self.config.MIN_STABLECOIN_ALLOCATION:
                return {
                    "valid": False,
                    "reason": f"Stablecoin allocation of {stablecoin_allocation:.1%} is below minimum of {self.config.MIN_STABLECOIN_ALLOCATION:.1%}"
                }
            
            # Plan is valid
            return {
                "valid": True,
                "message": "Rebalance plan meets risk constraints"
            }
        except Exception as e:
            logger.error(f"Error validating rebalance plan: {str(e)}")
            return {
                "valid": False,
                "reason": f"Error validating plan: {str(e)}"
            }
