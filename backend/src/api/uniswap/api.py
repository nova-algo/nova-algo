from dataclasses import dataclass
from typing import Dict, Optional, Set
import web3
from web3 import Web3
import asyncio
import logging

@dataclass
class BotStatus:
    chain_id: int
    current_block: int = 0
    current_block_timestamp: int = 0
    base_fee: int = 0
    base_fee_next: int = 0
    live: bool = False
    first_block: int = 0
    first_event: int = 0
    watching_blocks: bool = False
    watching_events: bool = False
    executor_balance: int = 0
    average_blocktime: float = 12.0
    paused: bool = False
    operator_balance: int = 0
    processing_tx: bool = False
    number_of_tx_processing: int = 0

class UniswapAPI:
    def __init__(self, web3_provider: Web3):
        self.w3 = web3_provider
        self.bot_status = BotStatus(chain_id=self.w3.eth.chain_id)
        self.events = asyncio.Queue()
        self.pending_tx = {}
        self.backrun_hashes = set()
