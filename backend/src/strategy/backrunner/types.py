from dataclasses import dataclass
from typing import Optional, Dict, Any
from web3.types import TxParams
from hexbytes import HexBytes

@dataclass
class BotStatus:
    chain_id: int
    current_block: int
    base_fee: int
    base_fee_next: Optional[int]
    executor_balance: int = 0
    operator_balance: int = 0
    average_blocktime: float = 12.0

@dataclass
class BackrunTx:
    tx: Optional[Dict[str, Any]]
    raw: HexBytes
    hash: HexBytes 