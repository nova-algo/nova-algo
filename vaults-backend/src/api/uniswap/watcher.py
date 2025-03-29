import asyncio
from typing import Dict, Set, Deque
from web3 import Web3
import logging
from ...common.config import UniswapConfig
from .processor import TransactionProcessor


logger = logging.getLogger(__name__)

class UniswapWatcher:
    def __init__(
        self,
        w3: Web3,
        processor: TransactionProcessor,
        config: UniswapConfig
    ):
        self.w3 = w3
        self.processor = processor
        self.config = config
        self.events: Deque = asyncio.Queue()
        self.pending_tx: Dict = {}
        self.backrun_hashes: Set = set()
        
    async def start(self):
        """Start the subscription watcher"""
        async for watcher in Web3.persistent_websocket(
            Web3.WebsocketProviderV2(endpoint_uri=self.config.NODE_WEBSOCKET_URI)
        ):
            try:
                # Subscribe to events
                events_sub = await watcher.eth.subscribe('logs', {})
                blocks_sub = await watcher.eth.subscribe('newHeads')
                pending_sub = await watcher.eth.subscribe(
                    'newPendingTransactions',
                    self.config.SUBSCRIBE_TO_FULL_TRANSACTIONS
                )
                
                logger.info(f"Subscribed to events: {events_sub}")
                logger.info(f"Subscribed to blocks: {blocks_sub}")
                logger.info(f"Subscribed to pending tx: {pending_sub}")
                
                async for message in watcher.ws.process_subscriptions():
                    sub_id = message["subscription"]
                    
                    if sub_id == events_sub:
                        await self._handle_event(message)
                    elif sub_id == blocks_sub:
                        await self._handle_block(message)
                    elif sub_id == pending_sub:
                        await self._handle_pending_tx(message)
                        
            except Exception as e:
                logger.error(f"Subscription error: {e}")
                continue
                
    async def _handle_event(self, message: Dict):
        """Handle incoming events"""
        self.events.append(message)
        
    async def _handle_block(self, message: Dict):
        """Handle new blocks"""
        block_number = int(message["result"]["number"], 16)
        logger.info(f"New block: {block_number}")
        
    async def _handle_pending_tx(self, message: Dict):
        """Handle pending transactions"""
        await self.processor.process_transaction(
            message["result"]["hash"] if self.config.SUBSCRIBE_TO_FULL_TRANSACTIONS
            else message["result"]
        ) 