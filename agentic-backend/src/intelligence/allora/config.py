"""
Configuration system for Allora integration
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, validator
from .models import AssetProfile

class AlloraConfig(BaseModel):
    """Configuration for Allora integration"""
    api_key: str
    base_url: str = "https://api.allora.network"
    cache_ttl: int = 300  # default cache TTL in seconds
    
    # Default weights for different types of assets
    default_weights: Dict[str, Dict[str, float]] = {
        "crypto": {
            "sentiment": 0.25,
            "below_median": 0.25,
            "volatility": 0.25,
            "trend": 0.25
        },
        "stocks": {
            "sentiment": 0.20,
            "below_median": 0.30,
            "volatility": 0.20,
            "trend": 0.30
        },
        "commodities": {
            "sentiment": 0.15,
            "below_median": 0.35,
            "volatility": 0.20,
            "trend": 0.30
        }
    }
    
    # Manipulation thresholds
    manipulation_thresholds: Dict[str, float] = {
        "established": 0.7,  # Established assets (BTC, ETH)
        "mature": 0.6,       # Mature assets (SOL, DOT)
        "new": 0.5           # New assets (less than 1 year old)
    }
    
    # Minimum days between rebalancing
    min_rebalance_days: int = 7
    
    # Cost-benefit ratio threshold for rebalancing
    # Potential benefit must exceed costs by at least this factor
    rebalance_cost_benefit_ratio: float = 2.0
    
    @validator('min_rebalance_days')
    def validate_min_days(cls, v):
        if v < 1:
            raise ValueError('Minimum days between rebalancing must be at least 1')
        return v
        
    @validator('rebalance_cost_benefit_ratio')
    def validate_ratio(cls, v):
        if v < 1.0:
            raise ValueError('Rebalance cost-benefit ratio must be at least 1.0')
        return v

class AssetProfiles:
    """
    Manager for asset-specific profiles
    
    Implements Rose Heart's advice of having asset-specific instruction sets
    """
    def __init__(self):
        # Load default asset profiles
        self.profiles: Dict[str, AssetProfile] = {
            # Bitcoin: Rose Heart noted it tends to remain below median
            "BTC": AssetProfile(
                symbol="BTC",
                name="Bitcoin",
                is_new_asset=False,
                topic_keys=["BTC_5min", "BTC_24h"],
                sentiment_weight=0.25,
                statistical_weight=0.75,
                manipulation_threshold=0.7  # Established asset
            ),
            
            # Ethereum
            "ETH": AssetProfile(
                symbol="ETH",
                name="Ethereum",
                is_new_asset=False,
                topic_keys=["ETH_5min", "ETH_24h"],
                sentiment_weight=0.25,
                statistical_weight=0.75,
                manipulation_threshold=0.7  # Established asset
            ),
            
            # Solana
            "SOL": AssetProfile(
                symbol="SOL",
                name="Solana",
                is_new_asset=False,
                topic_keys=["SOL_10min", "SOL_24h"],
                sentiment_weight=0.3,  # Slightly higher sentiment weight
                statistical_weight=0.7,
                manipulation_threshold=0.6  # Mature asset
            ),
            
            # USDC - stablecoin
            "USDC": AssetProfile(
                symbol="USDC",
                name="USD Coin",
                is_new_asset=False,
                topic_keys=[],  # No specific topics for stablecoins
                sentiment_weight=0.1,  # Low sentiment weight for stablecoins
                statistical_weight=0.9,
                manipulation_threshold=0.8  # Less susceptible to manipulation
            ),
            
            # USDT - stablecoin
            "USDT": AssetProfile(
                symbol="USDT",
                name="Tether",
                is_new_asset=False,
                topic_keys=[],  # No specific topics for stablecoins
                sentiment_weight=0.1,  # Low sentiment weight for stablecoins
                statistical_weight=0.9,
                manipulation_threshold=0.8  # Less susceptible to manipulation
            )
        }
    
    def get_profile(self, symbol: str) -> AssetProfile:
        """Get asset profile, creating default if not exists"""
        symbol = symbol.upper()
        if symbol not in self.profiles:
            # Create default profile
            return AssetProfile(
                symbol=symbol,
                is_new_asset=True,  # Assume new asset if not in profiles
                topic_keys=[],
                sentiment_weight=0.2,
                statistical_weight=0.8,
                manipulation_threshold=0.5  # Lower threshold for new assets
            )
        return self.profiles[symbol]
    
    def add_profile(self, profile: AssetProfile) -> None:
        """Add or update asset profile"""
        self.profiles[profile.symbol.upper()] = profile
    
    def get_all_profiles(self) -> List[AssetProfile]:
        """Get all asset profiles"""
        return list(self.profiles.values())

# Singleton instance
asset_profiles = AssetProfiles()

def get_asset_profile(symbol: str) -> AssetProfile:
    """Get asset profile for a symbol"""
    return asset_profiles.get_profile(symbol)

def get_all_asset_profiles() -> List[AssetProfile]:
    """Get all asset profiles"""
    return asset_profiles.get_all_profiles()

def add_asset_profile(profile: AssetProfile) -> None:
    """Add or update asset profile"""
    asset_profiles.add_profile(profile) 