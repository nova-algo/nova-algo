"""
Module: main.py
Entry point of the backrunner that sets up logging, loads historical data,
initializes shared state, and starts asynchronous tasks.
"""

import asyncio
import logging
import ujson
from concurrent.futures import ProcessPoolExecutor
from web3 import Web3
import signal

from .config import NODE_IPC_PATH, DRY_RUN, DATA_DIR
from .builders import send_to_builders
from .pending import process_pending_transaction
from .tracker import track_balance
from .types import BotStatus, BackrunTx
from .blacklist import BlacklistManager
from .simulation import simulate_bundle
from .events import subscribe_to_events

logger = logging.getLogger("ethereum_backrun_mempool_uniswap_curve_cycle")
logger.propagate = False
logger.setLevel(logging.INFO)
logger_formatter = logging.Formatter("%(levelname)s - %(message)s")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logger_formatter)
logger.addHandler(stream_handler)

async def main():
    # Setup signal handlers
    for sig in (signal.SIGINT, signal.SIGTERM):
        asyncio.get_running_loop().add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))

    # Connect to Web3 using IPC provider.
    w3 = Web3(Web3.IPCProvider(NODE_IPC_PATH))
    if not w3.isConnected():
        logger.error("Failed to connect to the node.")
        return

    # Load historical submitted bundles.
    try:
        with open("submitted_bundles.json") as file:
            SUBMITTED_BUNDLES = ujson.load(file)
    except FileNotFoundError:
        SUBMITTED_BUNDLES = {}
        with open("submitted_bundles.json", "w") as file:
            ujson.dump(SUBMITTED_BUNDLES, file, indent=2)
    logger.info(f"Found {len(SUBMITTED_BUNDLES)} submitted bundles")

    # Load blacklisted pools, tokens, and arbs as needed.
    # ...

    # Initialize core components
    blacklist_manager = BlacklistManager()
    blacklist_manager.load_blacklists(DATA_DIR)
    
    bot_status = BotStatus(
        chain_id=1,
        current_block=w3.eth.block_number,
        base_fee=w3.eth.get_block('latest')['baseFeePerGas'],
        base_fee_next=None
    )

    # Create tasks
    tasks = set()

    # Create any additional shared state (e.g., dictionary for arbitrage opportunities)
    all_arbs = {}  # This should be populated accordingly
    
    #     process_pool = ProcessPoolExecutor(max_workers=4)

    # # Create asynchronous tasks for tracking balance and system watchdog.
    # asyncio.create_task(track_balance(w3, all_arbs, bot_status))
    # asyncio.create_task(watchdog(bot_status))
    
    # # Main loop to process pending transactions and other tasks.
    # while True:
    #     await asyncio.sleep(1)
    tasks.add(asyncio.create_task(track_balance(w3, bot_status, all_arbs)))
    tasks.add(asyncio.create_task(subscribe_to_events(w3, bot_status, blacklist_manager)))

    # Main event loop
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

async def shutdown():
    logger.info("Shutdown signal received. Exiting...")
    # Add additional cleanup logic if necessary.
    for task in asyncio.all_tasks():
        task.cancel()
    await asyncio.sleep(1)
    exit(0)

if __name__ == "__main__":
    if not DRY_RUN:
        logger.info("")
        logger.info("***************************************")
        logger.info("*** DRY RUN DISABLED - BOT IS LIVE! ***")
        logger.info("***************************************")
        logger.info("")
    asyncio.run(main()) 