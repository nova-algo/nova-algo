import asyncio
from typing import Dict, Set, Deque, Optional
from collections import deque
import logging
from web3 import Web3
from .managers import PoolManager
from .pools.base import Pool
from ..common.types import BlockInfo

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

class PoolMonitor:
    def __init__(self, w3: Web3, pools: Set[Pool]):
        self.w3 = w3
        self.pools = pools
        self.latest_block: Optional[BlockInfo] = None
        
    async def _handle_event(self, message: Dict):
        """Handle incoming events (Sync, Swap, etc)"""
        
        event_type = message.get("event")
        if not event_type:
            return
            
        pool_address = message.get("address")
        if not pool_address:
            return
            
        pool = next((p for p in self.pools if p.address == pool_address), None)
        if not pool:
            return
            
        try:
            if event_type == "Sync":
                await self._handle_sync_event(pool, message)
            elif event_type == "Swap":
                await self._handle_swap_event(pool, message)
            # Add other event types as needed
        except Exception as e:
            logger.error(f"Failed to handle {event_type} event: {e}")
            
    async def _handle_block(self, message: Dict):
        """Handle new block notifications"""
        
        try:
            block_number = int(message["number"], 16)
            block_timestamp = int(message["timestamp"], 16)
            base_fee = int(message["baseFeePerGas"], 16)
            
            self.latest_block = BlockInfo(
                number=block_number,
                timestamp=block_timestamp,
                base_fee=base_fee
            )
            
            # Update pool states if needed
            for pool in self.pools:
                await pool.update_state(block_number)
                
        except Exception as e:
            logger.error(f"Failed to handle new block: {e}")
            
    async def _handle_pending_tx(self, message: Dict):
        """Handle pending transaction notifications"""
        
        try:
            tx_hash = message.get("hash")
            if not tx_hash:
                return
                
            # Get full transaction
            tx = await self.w3.eth.get_transaction(tx_hash)
            
            # Check if transaction affects any of our pools
            affected_pools = self._get_affected_pools(tx)
            
            # Update pool states if needed
            for pool in affected_pools:
                await pool.update_state_from_pending_tx(tx)
                
        except Exception as e:
            logger.error(f"Failed to handle pending transaction: {e}") 