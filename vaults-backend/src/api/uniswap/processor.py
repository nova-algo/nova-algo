from typing import Optional, Dict
from web3 import Web3
from eth_typing import HexBytes
import logging
from degenbot import UniswapTransaction, ArbitrageError
from .helpers.uniswap_curve_cycle import UniswapCurveCycle

logger = logging.getLogger(__name__)

class TransactionProcessor:
    def __init__(self, w3: Web3, config: Dict):
        self.w3 = w3
        self.config = config
        
    async def process_transaction(
        self,
        tx_hash: HexBytes,
        transaction: Optional[dict] = None,
        raw_tx: Optional[HexBytes] = None
    ):
        """Process a single pending transaction"""
        
        if transaction is None:
            try:
                transaction = dict(self.w3.eth.get_transaction(tx_hash))
            except Exception as e:
                logger.error(f"Failed to get transaction: {e}")
                return

        # Create UniswapTransaction helper
        try:
            tx_helper = UniswapTransaction(
                tx_hash=tx_hash,
                chain_id=self.config['chain_id'],
                func_name=transaction['input'][:10],
                func_params=transaction['input'][10:],
                tx_nonce=transaction['nonce'],
                tx_value=transaction['value'],
                tx_sender=transaction['from'],
                router_address=transaction['to']
            )
        except Exception as e:
            logger.error(f"Failed to create tx helper: {e}")
            return

        # Simulate transaction
        try:
            sim_results = tx_helper.simulate()
        except ArbitrageError as e:
            logger.error(f"Simulation failed: {e}")
            return
            
        # Calculate arbitrage opportunities using affected pools
        arb_results = []
        for pool in sim_results.affected_pools:
            for arb_helper in pool.get_arbitrage_helpers():
                if isinstance(arb_helper, UniswapCurveCycle):
                    try:
                        result = await arb_helper.calculate_arbitrage(
                            override_state=sim_results.pool_states
                        )
                        if result.profitable:
                            arb_results.append(result)
                    except Exception as e:
                        logger.error(f"Arbitrage calculation failed: {e}")
                        continue
                        
        return arb_results