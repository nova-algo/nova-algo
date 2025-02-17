from typing import Dict, Optional
from decimal import Decimal
from web3 import Web3

from .base import LiquidityPool
from ..constants import UNISWAP_V2_PAIR_ABI

class UniswapV2Pool(LiquidityPool):
    """Implementation of Uniswap V2 pool"""
    
    def __init__(self, address: str, token0: str, token1: str):
        super().__init__(address, token0, token1)
        self.fee = Decimal('0.003')  # 0.3% fee

    def get_amounts_out(self, token_in: str, amount_in: int) -> int:
        """Calculate output amount using constant product formula"""
        if not self.state:
            raise ValueError("Pool state not initialized")
            
        reserve_in = self.state['reserve0'] if token_in == self.token0 else self.state['reserve1']
        reserve_out = self.state['reserve1'] if token_in == self.token0 else self.state['reserve0']
        
        amount_in_with_fee = amount_in * (1 - self.fee)
        numerator = amount_in_with_fee * reserve_out
        denominator = reserve_in + amount_in_with_fee
        
        return numerator // denominator

    def update_state(self, new_state: Dict) -> None:
        """Update pool reserves"""
        self.state.update(new_state) 