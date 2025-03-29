from typing import Dict, List, Optional
from decimal import Decimal
from ...api.uniswap.pools.base import LiquidityPool
from ...common.types import ArbitrageResult, SwapInfo
from degenbot import UniswapV2LiquidityPool, CurveStableswapPool

class UniswapCurveCycle:
    """
    Helper class for Uniswap → Curve → Uniswap arbitrage cycles.
    Handles calculation and execution of arbitrage opportunities.
    """
    
    def __init__(self, pools: List[LiquidityPool], initial_amount: Decimal):
        self.pools = pools
        self.initial_amount = initial_amount
        self.min_profit = Decimal('0.001')  # 0.1% minimum profit
        self.curve_discount_factor = Decimal('0.9999')  # 0.01% reduction for Curve calcs
        
    async def calculate_arbitrage(
        self,
        override_state: Optional[Dict] = None
    ) -> ArbitrageResult:
        """Calculate optimal arbitrage for the current cycle"""
        
        # Apply state overrides if provided
        if override_state:
            for pool in self.pools:
                if pool.address in override_state:
                    pool.apply_state_override(override_state[pool.address])
                    
        # Calculate optimal input amount using binary search
        best_amount = Decimal('0')
        best_profit = Decimal('0')
        
        left = self.initial_amount / 100  # Start with 1% of initial amount
        right = self.initial_amount * 2
        
        while left < right:
            mid = (left + right) / 2
            
            # Calculate profit for current amount
            amount_out = mid
            for pool in self.pools:
                if isinstance(pool, CurveStableswapPool):
                    amount_out = amount_out * self.curve_discount_factor
                amount_out = pool.get_amount_out(amount_out)
                
            profit = amount_out - mid
            
            if profit > best_profit:
                best_profit = profit
                best_amount = mid
                
            if profit > self.min_profit:
                left = mid * Decimal('1.001')  # Increase by 0.1%
            else:
                right = mid * Decimal('0.999')  # Decrease by 0.1%
                
        # Build final swap sequence
        final_swaps = []
        amount_out = best_amount
        
        for pool in self.pools:
            amount_out = pool.get_amount_out(amount_out)
            final_swaps.append(SwapInfo(
                pool_address=pool.address,
                amount_in=amount_out,
                min_amount_out=int(amount_out * Decimal('0.995'))  # 0.5% slippage
            ))
            
        return ArbitrageResult(
            profitable=best_profit > self.min_profit,
            profit_amount=int(best_profit),
            swaps=final_swaps
        ) 