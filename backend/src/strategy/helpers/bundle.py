from typing import List, Dict, Optional
from web3 import Web3
from eth_account.account import Account
import logging
from ...common.types import BackrunTx, ArbitrageResult

logger = logging.getLogger(__name__)

class BundleBuilder:
    """Handles creation and submission of backrun bundles"""
    
    def __init__(
        self,
        w3: Web3,
        account: Account,
        executor_address: str,
        executor_abi: str
    ):
        self.w3 = w3
        self.account = account
        self.executor = w3.eth.contract(
            address=executor_address,
            abi=executor_abi
        )

    async def create_backrun_bundle(
        self,
        arb_result: ArbitrageResult,
        tx_to_backrun: BackrunTx,
        target_block: int,
        bribe_bips: int = 9500  # 95% default bribe
    ) -> Optional[Dict]:
        """Create a backrun bundle for the given arbitrage"""
        try:
            # Build the bundle payloads
            payloads = self._build_payloads(arb_result)
            
            # Create the backrun transaction
            backrun_tx = self._create_backrun_tx(
                payloads=payloads,
                bribe_bips=bribe_bips
            )
            
            # Build the complete bundle
            bundle = {
                "txs": [
                    tx_to_backrun.raw.hex(),  # Original tx
                    backrun_tx.rawTransaction.hex()  # Our backrun
                ],
                "revertingTxHashes": [],
                "targetBlock": target_block,
                "maxGasLimit": 2_000_000,  # Configurable
                "replacementUuid": None
            }
            
            return bundle
            
        except Exception as e:
            logger.error(f"Bundle creation error: {e}")
            return None

    def _build_payloads(self, arb_result: ArbitrageResult) -> List[Dict]:
        """Build executor payloads from arbitrage result"""
        payloads = []
        
        for swap in arb_result.swaps:
            payload = {
                'target': swap.pool_address,
                'calldata': swap.get_calldata(),
                'value': 0
            }
            payloads.append(payload)
            
        return payloads

    def _create_backrun_tx(self, payloads: List[Dict], bribe_bips: int) -> Dict:
        """Create and sign the backrun transaction"""
        nonce = self.w3.eth.get_transaction_count(self.account.address)
        
        # Get current gas prices
        base_fee = self.w3.eth.get_block('latest')['baseFeePerGas']
        priority_fee = self.w3.eth.max_priority_fee
        max_fee = base_fee * 2 + priority_fee
        
        # Build transaction
        tx = {
            'from': self.account.address,
            'to': self.executor.address,
            'nonce': nonce,
            'gas': 500000,  # Estimate this based on payload size
            'maxFeePerGas': max_fee,
            'maxPriorityFeePerGas': priority_fee,
            'data': self.executor.encodeABI(
                fn_name='execute_payloads',
                args=[payloads, True, bribe_bips]
            )
        }
        
        # Sign transaction
        signed_tx = self.account.sign_transaction(tx)
        return signed_tx