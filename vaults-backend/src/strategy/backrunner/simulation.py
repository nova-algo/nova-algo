from typing import Tuple, List, Optional, Dict, Any
from web3.types import TxReceipt
from hexbytes import HexBytes
from degenbot import AnvilFork
from .types import BackrunTx

async def simulate_bundle(
    bundle: Tuple[BackrunTx, HexBytes, Dict[str, Any]],
    simulator: AnvilFork,
    pre_check: bool = True,
) -> Tuple[List[bool], List[Optional[TxReceipt]]]:
    """
    Execute the transaction bundle against the fork.
    Returns a tuple of success values and transaction receipts:
      - success: List[bool]
      - receipts: List[Dict]
    """
    mempool_tx, arb_tx_raw, arb_tx = bundle
    success: List[bool] = [False] * 2
    
    mempool_tx_receipt: Optional[TxReceipt] = None
    arb_tx_receipt: Optional[TxReceipt] = None

    try:
        mempool_tx_hash = simulator.w3.eth.send_raw_transaction(mempool_tx.raw)
        mempool_tx_receipt = simulator.w3.eth.wait_for_transaction_receipt(
            mempool_tx_hash, 
            timeout=0.25
        )
    except Exception as e:
        print(f"(simulate_bundle.send_transaction): {e}")
        raise
    else:
        if mempool_tx_receipt and mempool_tx_receipt["status"] == 1:
            success[0] = True

    if pre_check:
        try:
            simulator.w3.eth.call(arb_tx)
        except Exception as e:
            print(f"eth_call failed for arb tx - {type(e)}: {e}")
            print(f"{arb_tx=}")

    try:
        arb_tx_hash = simulator.w3.eth.send_raw_transaction(arb_tx_raw)
        arb_tx_receipt = simulator.w3.eth.wait_for_transaction_receipt(
            arb_tx_hash,
            timeout=0.25
        )
    except Exception as e:
        print(f"(send_raw_transaction): {e}")
        raise
    else:
        if arb_tx_receipt and arb_tx_receipt["status"] == 1:
            success[1] = True

    return success, [mempool_tx_receipt, arb_tx_receipt] 