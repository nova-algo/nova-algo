"""
Configuration Manager

Manages asset-specific profiles, market condition weights, and application-wide settings.
Follows the singleton pattern for consistent access throughout the application.
"""
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class AssetProfile(BaseModel):
    """Asset-specific configuration profile"""
    symbol: str
    name: Optional[str] = None
    asset_type: str = "crypto"  # crypto, stock, commodity
    is_stablecoin: bool = False
    is_new_asset: bool = False  # less than 1 year old
    topic_ids: Dict[str, int] = {}  # Mapping of timeframe to Allora topic ID
    
    # Default weights as recommended by Rose Heart
    sentiment_weight: float = 0.25
    statistical_weight: float = 0.75
    
    # Market condition specific weights
    weights_by_condition: Dict[str, Dict[str, float]] = {
        "normal": {
            "sentiment": 0.25,
            "below_median": 0.25,
            "volatility": 0.25,
            "trend": 0.25
        },
        "volatile": {
            "sentiment": 0.15,
            "below_median": 0.20,
            "volatility": 0.40,
            "trend": 0.25
        },
        "bull": {
            "sentiment": 0.30,
            "below_median": 0.20,
            "volatility": 0.20,
            "trend": 0.30
        },
        "bear": {
            "sentiment": 0.35,
            "below_median": 0.25,
            "volatility": 0.15,
            "trend": 0.25
        }
    }
    
    # Risk parameters
    manipulation_threshold: float = 0.6
    min_rebalance_days: int = 7
    cost_benefit_ratio: float = 2.0
    max_allocation: float = 0.5  # maximum portfolio allocation
    
    def get_weights_for_condition(self, condition: str) -> Dict[str, float]:
        """Get weights for a specific market condition"""
        return self.weights_by_condition.get(
            condition, 
            self.weights_by_condition["normal"]
        )

class MarketConditionWeights(BaseModel):
    """Weights for different market conditions"""
    normal: Dict[str, float] = {
        "sentiment": 0.25,
        "statistical": 0.75
    }
    volatile: Dict[str, float] = {
        "sentiment": 0.15,
        "statistical": 0.85
    }
    bull: Dict[str, float] = {
        "sentiment": 0.30,
        "statistical": 0.70
    }
    bear: Dict[str, float] = {
        "sentiment": 0.35,
        "statistical": 0.65
    }

class ConfigManager:
    """
    Configuration Manager for the entire application
    
    Manages:
    - Asset-specific profiles
    - Market condition weights
    - Global application settings
    
    Implements singleton pattern for consistent access
    """
    
    _instance = None  # Singleton instance
    
    @classmethod
    def get_instance(cls):
        """Get or create the singleton instance"""
        if cls._instance is None:
            cls._instance = ConfigManager()
        return cls._instance
    
    def __init__(self):
        """Initialize configuration manager"""
        if ConfigManager._instance is not None:
            raise RuntimeError("ConfigManager is a singleton. Use get_instance() instead.")
            
        ConfigManager._instance = self
        
        # Load default asset profiles
        self.asset_profiles = self._load_default_asset_profiles()
        
        # Load market condition weights
        self.market_condition_weights = MarketConditionWeights()
        
        # Global settings
        self.settings = {
            "allora_api_key": os.environ.get("ALLORA_API_KEY", ""),
            "allora_base_url": os.environ.get("ALLORA_BASE_URL", "https://api.allora.network"),
            "enable_performance_tracking": True,
            "enable_manipulation_detection": True,
            "enable_trade_validation": True,
            "default_min_rebalance_days": 7,
            "default_cost_benefit_ratio": 2.0,
            "default_slippage_percent": 0.5,
            "log_level": os.environ.get("LOG_LEVEL", "INFO")
        }
    
    def _load_default_asset_profiles(self) -> Dict[str, AssetProfile]:
        """Load default asset profiles for common assets"""
        profiles = {}
        
        # Bitcoin profile
        # Rose Heart noted BTC tends to remain below median
        profiles["BTC"] = AssetProfile(
            symbol="BTC",
            name="Bitcoin",
            topic_ids={
                "5min": 14,  # Short-term
                "24h": 4     # Long-term
            },
            is_new_asset=False,
            manipulation_threshold=0.7,  # Less prone to manipulation
            weights_by_condition={
                "normal": {
                    "sentiment": 0.25,
                    "below_median": 0.30,  # Higher weight due to tendency to stay below median
                    "volatility": 0.20,
                    "trend": 0.25
                },
                "volatile": {
                    "sentiment": 0.15,
                    "below_median": 0.25,
                    "volatility": 0.40,
                    "trend": 0.20
                },
                "bull": {
                    "sentiment": 0.30,
                    "below_median": 0.20,
                    "volatility": 0.20,
                    "trend": 0.30
                },
                "bear": {
                    "sentiment": 0.35,
                    "below_median": 0.30,
                    "volatility": 0.15,
                    "trend": 0.20
                }
            }
        )
        
        # Ethereum profile
        profiles["ETH"] = AssetProfile(
            symbol="ETH",
            name="Ethereum",
            topic_ids={
                "5min": 13,  # Short-term
                "24h": 2     # Long-term
            },
            is_new_asset=False,
            manipulation_threshold=0.7  # Less prone to manipulation
        )
        
        # Solana profile
        profiles["SOL"] = AssetProfile(
            symbol="SOL",
            name="Solana",
            topic_ids={
                "10min": 5,  # Medium-term
                "24h": 6     # Long-term
            },
            sentiment_weight=0.3,  # Slightly higher weight for sentiment
            statistical_weight=0.7,
            manipulation_threshold=0.6  # Medium prone to manipulation
        )
        
        # USDC profile (stablecoin)
        profiles["USDC"] = AssetProfile(
            symbol="USDC",
            name="USD Coin",
            is_stablecoin=True,
            # Stablecoins don't have dedicated topics
            sentiment_weight=0.1,  # Low sentiment influence for stablecoins
            statistical_weight=0.9,
            manipulation_threshold=0.8,  # Very low manipulation risk
            max_allocation=0.8   # Can have high allocation as it's stable
        )
        
        # USDT profile (stablecoin)
        profiles["USDT"] = AssetProfile(
            symbol="USDT",
            name="Tether",
            is_stablecoin=True,
            # Stablecoins don't have dedicated topics
            sentiment_weight=0.1,  # Low sentiment influence for stablecoins
            statistical_weight=0.9,
            manipulation_threshold=0.8  # Very low manipulation risk
        )
        
        return profiles
    
    def get_asset_profile(self, symbol: str) -> AssetProfile:
        """
        Get an asset profile by symbol
        
        Args:
            symbol: Asset symbol (e.g., "BTC")
            
        Returns:
            AssetProfile for the asset, or a default profile if not found
        """
        symbol = symbol.upper()
        if symbol in self.asset_profiles:
            return self.asset_profiles[symbol]
            
        # Create a default profile for unknown assets
        # Assume new assets (more risky) if not in our known list
        logger.info(f"Creating default profile for unknown asset: {symbol}")
        return AssetProfile(
            symbol=symbol,
            is_new_asset=True,
            manipulation_threshold=0.5  # Higher manipulation risk for unknown assets
        )
    
    def get_weights_for_condition(self, symbol: str, condition: str) -> Dict[str, float]:
        """
        Get weights for a specific asset and market condition
        
        Args:
            symbol: Asset symbol (e.g., "BTC")
            condition: Market condition (normal, volatile, bull, bear)
            
        Returns:
            Dictionary with weights for different signals
        """
        profile = self.get_asset_profile(symbol)
        return profile.get_weights_for_condition(condition)
    
    def add_asset_profile(self, profile: AssetProfile) -> None:
        """Add or update an asset profile"""
        self.asset_profiles[profile.symbol.upper()] = profile
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a global setting value"""
        return self.settings.get(key, default)
    
    def update_setting(self, key: str, value: Any) -> None:
        """Update a global setting"""
        self.settings[key] = value
    
    def get_allora_topic_id(self, symbol: str, timeframe: str = "5min") -> Optional[int]:
        """
        Get Allora topic ID for a specific asset and timeframe
        
        Args:
            symbol: Asset symbol (e.g., "BTC")
            timeframe: Time period (5min, 10min, 24h, etc.)
            
        Returns:
            Topic ID or None if not available
        """
        profile = self.get_asset_profile(symbol)
        return profile.topic_ids.get(timeframe)
        
# Convenience function to get config manager instance
def get_config_manager() -> ConfigManager:
    """Get the singleton ConfigManager instance"""
    return ConfigManager.get_instance() 