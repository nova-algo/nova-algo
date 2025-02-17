from typing import Dict, Optional
from src.api.uniswap.pools.base import LiquidityPool
from web3 import Web3
import logging
from .pools.v2 import UniswapV2Pool
from .pools.v3 import UniswapV3Pool
from .pools.curve import CurveStableswapPool

logger = logging.getLogger(__name__)

class PoolManager:
    """Base class for pool management"""
    def __init__(self, w3: Web3):
        self.w3 = w3
        self.pools: Dict[str, 'LiquidityPool'] = {}

    def get_pool(self, address: str) -> Optional['LiquidityPool']:
        return self.pools.get(address)

class UniswapV2PoolManager(PoolManager):
    """Manages Uniswap V2 pools"""
    def create_pool(self, address: str, token0: str, token1: str) -> UniswapV2Pool:
        pool = UniswapV2Pool(address, token0, token1)
        self.pools[address] = pool
        return pool

class UniswapV3PoolManager(PoolManager):
    """Manages Uniswap V3 pools"""
    def create_pool(self, address: str, token0: str, token1: str, fee: int) -> UniswapV3Pool:
        pool = UniswapV3Pool(address, token0, token1, fee)
        self.pools[address] = pool
        return pool 