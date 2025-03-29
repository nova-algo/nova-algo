from dataclasses import dataclass
from typing import Dict, Optional, Set, List, Callable
from web3 import Web3
import asyncio
import logging
from hexbytes import HexBytes

logger = logging.getLogger(__name__)

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
        self.pending_tx: Dict[HexBytes, dict] = {}
        self.backrun_hashes: Set[HexBytes] = set()
        self.pending_tx_handlers: List[Callable] = []
        self.new_block_handlers: List[Callable] = []
        self.event_handlers: List[Callable] = []
        
    async def initialize(self):
        """Initialize API connections and subscriptions"""
        try:
            # Check connection
            if not self.w3.is_connected():
                raise ConnectionError("Failed to connect to Web3 provider")
                
            # Initialize subscriptions
            await self._setup_subscriptions()
            
            self.bot_status.live = True
            logger.info("UniswapAPI initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize UniswapAPI: {e}")
            raise
            
    async def _setup_subscriptions(self):
        """Set up websocket subscriptions"""
        # Subscribe to new blocks
        self.new_blocks_subscription = await self.w3.eth.subscribe('newHeads')
        logger.info("Subscribed to new blocks")
        
        # Subscribe to pending transactions
        self.pending_tx_subscription = await self.w3.eth.subscribe(
            'pendingTransactions',
            {'includeTransactions': True}
        )
        logger.info("Subscribed to pending transactions")
        
        # Start subscription handlers
        asyncio.create_task(self._handle_subscriptions())
        
    async def _handle_subscriptions(self):
        """Handle incoming subscription messages"""
        while True:
            try:
                # Handle new blocks
                async for block in self.new_blocks_subscription:
                    await self._process_new_block(block)
                    
                # Handle pending transactions
                async for tx in self.pending_tx_subscription:
                    await self._process_pending_tx(tx)
                    
            except Exception as e:
                logger.error(f"Error in subscription handler: {e}")
                await asyncio.sleep(1)
                
    async def _process_new_block(self, block: dict):
        """Process new block data"""
        self.bot_status.current_block = block['number']
        self.bot_status.current_block_timestamp = block['timestamp']
        self.bot_status.base_fee = block['baseFeePerGas']
        
        # Notify block handlers
        for handler in self.new_block_handlers:
            try:
                await handler(block)
            except Exception as e:
                logger.error(f"Error in block handler: {e}")
                
    async def _process_pending_tx(self, tx: dict):
        """Process pending transaction"""
        tx_hash = tx['hash']
        if tx_hash in self.backrun_hashes:
            return
            
        self.pending_tx[tx_hash] = tx
        
        # Notify transaction handlers
        for handler in self.pending_tx_handlers:
            try:
                await handler(tx_hash, tx)
            except Exception as e:
                logger.error(f"Error in transaction handler: {e}")
                
    def on_pending_tx(self, handler: Callable):
        """Register pending transaction handler"""
        self.pending_tx_handlers.append(handler)
        
    def on_new_block(self, handler: Callable):
        """Register new block handler"""
        self.new_block_handlers.append(handler)
        
    def on_event(self, handler: Callable):
        """Register event handler"""
        self.event_handlers.append(handler)
        
    async def get_gas_price(self) -> int:
        """Get current gas price"""
        return await self.w3.eth.gas_price
        
    async def get_block(self, block_identifier: int) -> dict:
        """Get block by number"""
        return await self.w3.eth.get_block(block_identifier)
        
    async def get_transaction(self, tx_hash: HexBytes) -> dict:
        """Get transaction by hash"""
        return await self.w3.eth.get_transaction(tx_hash)
        
    async def send_transaction(self, transaction: dict) -> HexBytes:
        """Send transaction"""
        return await self.w3.eth.send_transaction(transaction)
        
    async def estimate_gas(self, transaction: dict) -> int:
        """Estimate gas for transaction"""
        return await self.w3.eth.estimate_gas(transaction)
        
    def decode_function_input(self, input_data: str) -> tuple:
        """Decode transaction input data"""
        return self.w3.eth.contract().decode_function_input(input_data)
