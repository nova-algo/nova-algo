"""Schemas for Kuru action provider."""

from decimal import Decimal
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field, validator, model_validator

from .constants import DEPOSITABLE_TOKENS  # Import from constants instead of defining here

# Define literals based on constants
SUPPORTED_TOKENS_LITERAL = Literal["usdc", "usdt", "dak", "chog", "yaki", "native"]
SUPPORTED_MARKETS_LITERAL = Literal["mon-usdc", "dak-mon", "chog-mon", "yaki-mon"]
SUPPORTED_NETWORKS_LITERAL = Literal["monad-testnet", "base-sepolia", "base-mainnet"]

class SwapParams(BaseModel):
    """Parameters for swap action."""
    from_token: SUPPORTED_TOKENS_LITERAL = Field(
        ..., 
        description="Token to swap from (usdc, usdt, dak, chog, yaki, or native for MON/ETH)"
    )
    to_token: SUPPORTED_TOKENS_LITERAL = Field(
        ..., 
        description="Token to swap to (usdc, usdt, dak, chog, yaki, or native for MON/ETH)"
    )
    amount_in: str = Field(..., description="Amount of from_token to swap (in decimal units)")
    min_amount_out: Optional[str] = Field(None, description="Minimum amount of to_token to receive")
    slippage_percentage: Optional[float] = Field(0.5, description="Slippage tolerance in percentage")
    network_id: SUPPORTED_NETWORKS_LITERAL = Field("monad-testnet", description="Network ID")
    market_id: SUPPORTED_MARKETS_LITERAL = Field(
        ..., 
        description="Market to trade on (mon-usdc, dak-mon, chog-mon, yaki-mon)"
    )
    
    @validator("amount_in")
    def validate_amount(cls, v):
        """Validate that amount is positive and a valid number."""
        try:
            amount = Decimal(v)
            if amount <= 0:
                raise ValueError("Amount must be positive")
            return v
        except:
            raise ValueError("Amount must be a valid number")

class OrderSpec(BaseModel):
    """Specification for a single order in a batch."""
    order_type: Literal["limit", "market"] = Field(..., description="Order type: 'limit' or 'market'")
    side: Literal["buy", "sell"] = Field(..., description="Order side: 'buy' or 'sell'")
    price: Optional[str] = Field(None, description="Limit price (required for limit orders)")
    size: str = Field(..., description="Order size")
    min_amount_out: Optional[str] = Field(None, description="Minimum amount out (for market orders)")
    post_only: bool = Field(False, description="Whether the order is post-only")
    cloid: Optional[str] = Field(None, description="Client order ID")

class LimitOrderParams(BaseModel):
    """Parameters for limit order action."""
    from_token: SUPPORTED_TOKENS_LITERAL = Field(
        ..., 
        description="Token to sell (usdc, usdt, dak, chog, yaki, or native for MON/ETH)"
    )
    to_token: SUPPORTED_TOKENS_LITERAL = Field(
        ..., 
        description="Token to buy (usdc, usdt, dak, chog, yaki, or native for MON/ETH)"
    )
    amount_in: str = Field(..., description="Amount of from_token to sell (in decimal units)")
    price: str = Field(..., description="Limit price in to_token per from_token")
    post_only: bool = Field(False, description="Whether to make the order post-only")
    network_id: SUPPORTED_NETWORKS_LITERAL = Field("monad-testnet", description="Network ID")
    market_id: SUPPORTED_MARKETS_LITERAL = Field(
        ..., 
        description="Market to trade on (mon-usdc, dak-mon, chog-mon, yaki-mon)"
    )

class OrderStatusParams(BaseModel):
    """Parameters for order status actions."""
    order_id: str = Field(..., description="Client order ID (cloid)")
    market_id: SUPPORTED_MARKETS_LITERAL = Field(
        ..., 
        description="Market to trade on (mon-usdc, dak-mon, chog-mon, yaki-mon)"
    )
    network_id: SUPPORTED_NETWORKS_LITERAL = Field("monad-testnet", description="Network ID")

class BatchOrderParams(BaseModel):
    """Parameters for batch orders action."""
    orders: List[OrderSpec] = Field(..., description="List of order specifications")
    market_id: SUPPORTED_MARKETS_LITERAL = Field(
        ..., 
        description="Market to trade on (mon-usdc, dak-mon, chog-mon, yaki-mon)"
    )
    network_id: SUPPORTED_NETWORKS_LITERAL = Field("monad-testnet", description="Network ID")

class MarginActionParams(BaseModel):
    """Parameters for margin account actions."""
    token_id: SUPPORTED_TOKENS_LITERAL = Field(
        ..., 
        description="Token to deposit/withdraw (on Monad testnet, only 'native' (MON) is supported)"
    )
    amount: Optional[str] = Field(None, description="Amount for deposit/withdraw")
    network_id: SUPPORTED_NETWORKS_LITERAL = Field("monad-testnet", description="Network ID")

    @model_validator(mode='after')
    def validate_token_for_network(self):
        """Validate that the token is supported for the specified network."""
        network_id = self.network_id
        token_id = self.token_id
        
        if network_id and token_id:
            if network_id == "monad-testnet" and token_id != "native":
                raise ValueError("On Monad testnet, only 'native' (MON) token can be deposited")
            elif network_id in DEPOSITABLE_TOKENS and token_id not in DEPOSITABLE_TOKENS[network_id]:
                raise ValueError(f"Token {token_id} is not supported for deposits on {network_id}")
        
        return self

class OrderbookParams(BaseModel):
    """Parameters for orderbook query."""
    market_id: SUPPORTED_MARKETS_LITERAL = Field(
        ..., 
        description="Market to query (mon-usdc, dak-mon, chog-mon, yaki-mon)"
    )
    network_id: SUPPORTED_NETWORKS_LITERAL = Field("monad-testnet", description="Network ID")