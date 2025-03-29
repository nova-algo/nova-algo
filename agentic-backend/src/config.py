from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """
    Application settings and configuration
    
    Loads from environment variables or uses defaults
    """
    # JWT Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-replace-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Database
    DATABASE_URL: str = "sqlite:///./data/rebalancr.db"
    #DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")

    ALLORA_API_KEY: str = os.getenv("ALLORA_API_KEY")
    AGENT_ID: str = os.getenv("AGENT_ID")
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    
    # Agent Configuration
    DEFAULT_REBALANCE_THRESHOLD: float = 5.0
    MAX_GAS_LIMIT_OPTIONS: dict = {
        "low": 1.0,
        "moderate": 1.5, 
        "high": 2.0
    }
    
    # External APIs
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    # GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    # DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    # DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY")
    
    PRIVY_APP_ID: str = os.getenv("PRIVY_APP_ID")
    PRIVY_APP_SECRET: Optional[str] = os.getenv("PRIVY_APP_SECRET")
    PRIVY_VERIFICATION_KEY: str = os.getenv("PRIVY_VERIFICATION_KEY")
    #PRIVY_WALLET_ID: Optional[str] = os.getenv("PRIVY_WALLET_ID")
    #PRIVY_API_KEY: str = os.getenv("PRIVY_API_KEY")  # API key for server wallets
    #PRIVY_WEBHOOK_SECRET: str = os.getenv("PRIVY_WEBHOOK_SECRET")  # For webhook verification

    CDP_API_KEY_NAME: Optional[str] = os.getenv("CDP_API_KEY_NAME")
    CDP_API_KEY_PRIVATE_KEY: Optional[str] = os.getenv("CDP_API_KEY_PRIVATE_KEY")
    
    # Privy configuration
    #PRIVY_PUBLIC_KEY: str = os.getenv("PRIVY_PUBLIC_KEY")  # For token verification
    
    # # Add this field to your existing Settings class
    # PRIVY_WALLET_ID: Optional[str] = None

    DATA_DIR: str = os.getenv("DATA_DIR", "./data")

    NETWORK_ID: str = os.getenv("NETWORK_ID", "monad-testnet")
    
    # Privy Server Wallets
    sqlite_db_path: str = "sqlite:///./data/rebalancr.db"
    wallet_data_dir: str = "./data/wallets"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Alternative solution: ignore extra fields

# Initialize settings once
settings = Settings()

def get_settings():
    return Settings()

"""
Rebalancr Configuration

This module provides configuration options for the rebalancing system, 
including integration with Allora, strategy parameters, and action providers.
"""

# Allora configuration
ALLORA_BASE_URL = os.environ.get("ALLORA_BASE_URL", "https://api.allora.network")

# Strategy configuration
STRATEGY_CONFIG = {
    # Minimum days between rebalancing as recommended by Rose Heart
    "MIN_REBALANCE_DAYS": 7,
    
    # Fee rate for transaction cost calculation
    "FEE_RATE": 0.001,  # 0.1%
    
    # Cost-benefit ratio threshold for rebalancing
    # Potential benefit must exceed costs by at least this factor
    "COST_BENEFIT_RATIO": 2.0,
    
    # Default asset weights for different risk profiles
    "DEFAULT_WEIGHTS": {
        "conservative": {"BTC": 0.2, "ETH": 0.2, "USDC": 0.6},
        "balanced": {"BTC": 0.3, "ETH": 0.3, "USDC": 0.4},
        "aggressive": {"BTC": 0.4, "ETH": 0.4, "USDC": 0.2}
    },
    
    # Signal weights - initially equal as Rose Heart suggested
    "SIGNAL_WEIGHTS": {
        "sentiment": 0.25,
        "below_median": 0.25,
        "volatility": 0.25,
        "trend": 0.25
    },
    
    # Special asset configurations
    "ASSET_CONFIG": {
        "BTC": {
            "sentiment_weight": 0.25,
            "statistical_weight": 0.75,
            "manipulation_threshold": 0.7
        },
        "ETH": {
            "sentiment_weight": 0.25,
            "statistical_weight": 0.75,
            "manipulation_threshold": 0.7
        },
        "USDC": {
            "sentiment_weight": 0.1,
            "statistical_weight": 0.9,
            "manipulation_threshold": 0.8
        }
    }
}

# Trade reviewer configuration
REVIEWER_CONFIG = {
    "USE_EXTERNAL_AI": os.environ.get("USE_EXTERNAL_AI", "false").lower() == "true",
    "REVIEWER_API_KEY": os.environ.get("REVIEWER_API_KEY", ""),
    "REVIEWER_API_URL": os.environ.get("REVIEWER_API_URL", "")
}


ALLORA_API_KEY: str = os.getenv("ALLORA_API_KEY")

# Supported networks
SUPPORTED_NETWORKS = [1, 56, 137, 42161, 10, 10143]  # Ethereum, BSC, Polygon, Arbitrum, Optimism, Monad

# Network RPC URLs
NETWORK_RPC_URLS = {
    1: os.environ.get("ETH_RPC_URL", ""),
    56: os.environ.get("BSC_RPC_URL", ""),
    137: os.environ.get("POLYGON_RPC_URL", ""),
    42161: os.environ.get("ARBITRUM_RPC_URL", ""),
    10: os.environ.get("OPTIMISM_RPC_URL", ""),
    10143: os.environ.get("MONAD_RPC_URL", "")
}

# Database configuration
DATABASE_CONFIG = {
    "URI": os.environ.get("DATABASE_URI", "sqlite:///rebalancr.db"),
    "POOL_SIZE": int(os.environ.get("DB_POOL_SIZE", "10")),
    "MAX_OVERFLOW": int(os.environ.get("DB_MAX_OVERFLOW", "20"))
}

def get_config() -> Dict[str, Any]:
    """Get the full configuration"""
    return {
        "ALLORA_API_KEY": ALLORA_API_KEY,
        "ALLORA_BASE_URL": ALLORA_BASE_URL,
        "STRATEGY": STRATEGY_CONFIG,
        "REVIEWER": REVIEWER_CONFIG,
        "SUPPORTED_NETWORKS": SUPPORTED_NETWORKS,
        "NETWORK_RPC_URLS": NETWORK_RPC_URLS,
        "DATABASE": DATABASE_CONFIG
    }

def get_strategy_config() -> Dict[str, Any]:
    """Get the strategy configuration"""
    return STRATEGY_CONFIG

def get_reviewer_config() -> Dict[str, Any]:
    """Get the trade reviewer configuration"""
    return REVIEWER_CONFIG

def get_network_rpc_url(network_id: int) -> str:
    """Get the RPC URL for a network"""
    return NETWORK_RPC_URLS.get(network_id, "")
