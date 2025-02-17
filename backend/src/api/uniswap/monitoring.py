import asyncio
from typing import Dict, Set, Deque
from collections import deque
import logging
from web3 import Web3
from .managers import PoolManager

logger = logging.getLogger(__name__)

class TransactionMonitor:
    """Monitors mempool and blocks for relevant transactions"""
    
    def __init__(
        self,
        w3: Web3,
        pool_manager: PoolManager,
        websocket_uri: str
    ):
        self.w3 = w3
        self.pool_manager = pool_manager
        self.websocket_uri = websocket_uri
        self.events: Deque = deque()
        self.pending_tx: Dict = {}
        self.backrun_hashes: Set = set()

    async def start_monitoring(self):
        """Start monitoring mempool and blocks"""
        async for ws in self.w3.websocket.persistent_websocket():
            try:
                # Subscribe to new blocks
                block_sub = await ws.eth.subscribe('newHeads')
                # Subscribe to pending transactions
                pending_sub = await ws.eth.subscribe('pendingTransactions')
                # Subscribe to relevant events (Sync, Swap, etc)
                events_sub = await ws.eth.subscribe('logs', {})
                
                async for message in ws.process_subscriptions():
                    await self._handle_subscription_message(message)
                    
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                continue

    async def _handle_subscription_message(self, message: Dict):
        """Handle incoming subscription messages"""
        subscription = message.get('subscription')
        if not subscription:
            return
            
        # Handle different types of messages (blocks, txs, events)
        if subscription.startswith('0x'):
            await self._handle_event(message)
        else:
            method = getattr(self, f'_handle_{subscription}_message', None)
            if method:
                await method(message) 