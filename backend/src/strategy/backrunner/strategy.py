from typing import Dict, Set
import asyncio
import logging
from web3 import Web3

from src.api.uniswap import UniswapAPI
from src.common.types import BackrunnerConfig
from .builders import send_to_builders
from .events import subscribe_to_events
from .pending import process_pending_transaction
from .tracker import track_balance
from .blacklist import BlacklistManager
from .types import BotStatus

logger = logging.getLogger(__name__)

class BackrunnerStrategy:
    def __init__(self, config: BackrunnerConfig, api: UniswapAPI):
        self.config = config
        self.api = api
        self.pending_tx: Dict = {}
        self.backrun_hashes: Set = set()
        self.blacklist_manager = BlacklistManager()
        self.bot_status = None
        self.tasks = set()
        
    async def init(self):
        """Initialize strategy components"""
        await self.api.initialize()
        
        # Initialize blacklist
        self.blacklist_manager.load_blacklists(self.config.data_dir)
        
        # Initialize bot status
        w3 = self.api.w3
        current_block = w3.eth.get_block('latest')
        self.bot_status = BotStatus(
            chain_id=w3.eth.chain_id,
            current_block=current_block['number'],
            base_fee=current_block['baseFeePerGas'],
            base_fee_next=None
        )
        
    async def execute(self):
        """Execute strategy"""
        try:
            # Add core monitoring tasks
            self.tasks.add(asyncio.create_task(
                track_balance(self.api.w3, self.bot_status, self.api.all_arbs)
            ))
            self.tasks.add(asyncio.create_task(
                subscribe_to_events(self.api.w3, self.bot_status, self.blacklist_manager)
            ))
            
            # Main execution loop
            await asyncio.gather(*self.tasks)
            
        except asyncio.CancelledError:
            # Handle graceful shutdown
            for task in self.tasks:
                task.cancel()
            await asyncio.gather(*self.tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Error in backrunner execution: {e}")
            raise 
