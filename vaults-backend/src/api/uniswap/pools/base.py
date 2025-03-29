from abc import ABC, abstractmethod
from typing import Dict, Optional, Set
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class LiquidityPool(ABC):
    """Base class for all liquidity pool implementations"""
    
    def __init__(self, address: str, token0: str, token1: str):
        self.address = address
        self.token0 = token0
        self.token1 = token1
        self.state: Dict = {}
        self.arbitrage_helpers: Set = set()

    def register_arbitrage_helper(self, helper: 'ArbitrageHelper') -> None:
        """Register an arbitrage helper that uses this pool"""
        self.arbitrage_helpers.add(helper)
        
    def get_arbitrage_helpers(self) -> Set['ArbitrageHelper']:
        """Get all arbitrage helpers using this pool"""
        return self.arbitrage_helpers

    @abstractmethod
    def get_amounts_out(self, token_in: str, amount_in: int) -> int:
        """Calculate output amount for a given input"""
        pass

    @abstractmethod
    def update_state(self, new_state: Dict) -> None:
        """Update pool state"""
        pass 