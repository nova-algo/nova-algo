"""
Module: pending.py
Contains process_pending_transaction function which processes pending transactions,
matches profitable arbitrage calculations and dispatches backrun transactions.
"""

import asyncio
import time
import logging
from typing import Dict, Set, Optional
from hexbytes import HexBytes
import aiohttp
import web3

from degenbot.arbitrage import UniswapCurveCycle
from .builders import send_to_builders
from .types import BotStatus, BackrunTx
from .blacklist import BlacklistManager

logger = logging.getLogger(__name__)

async def process_pending_transaction(
    w3: web3.Web3,
    bot_status: BotStatus,  # Now using the proper type
    pending_tx: Dict[HexBytes, dict],
    http_session: aiohttp.ClientSession,
    all_arbs: Dict[str, UniswapCurveCycle],
    tasks: Set[asyncio.Task],
    backrun_hashes: Set,
    process_pool: "ProcessPoolExecutor",  # adjust type hint accordingly
    transaction_hash: HexBytes,
    blacklist_manager: BlacklistManager,  # Add blacklist manager
    transaction: Optional[dict] = None,
    raw_transaction: Optional[HexBytes] = None,
) -> None:
    """
    Process pending transaction:
    The function processes the pending transaction, matches profitable arbitrage calculations
    and dispatches transactions accordingly.
    """
    # Use blacklist manager to check pools/tokens
    if blacklist_manager.is_pool_blacklisted(pool_address):
        logger.debug(f"Skipping blacklisted pool: {pool_address}")
        return
        
    if blacklist_manager.is_token_blacklisted(token_address):
        logger.debug(f"Skipping blacklisted token: {token_address}")
        return
    
    # Create BackrunTx instance
    backrun_tx = BackrunTx(
        tx=transaction,
        raw=raw_transaction,
        hash=transaction_hash
    )
    
    all_profitable_calc_results = []  # Replace with real calculation results
    all_profitable_arbs = []  # Replace with real arbitrage opportunities
    results_by_arb_id = {}
    _start = time.perf_counter()

    # Process each profitable arbitrage.
    for calc_result, arb in zip(all_profitable_calc_results, all_profitable_arbs, strict=True):
        # if TYPE_CHECKING:
        results_by_arb_id[arb.id] = calc_result

    if not all_profitable_arbs:
        return

    arbs_without_overlap = set()
    while True:
        most_profitable_arb = all_profitable_arbs.pop(0)
        if __import__("typing").TYPE_CHECKING:
            assert most_profitable_arb is not None
        arbs_without_overlap.add(most_profitable_arb)

        conflicting_arbs = [
            arb_helper
            for arb_helper in all_profitable_arbs
            if set(most_profitable_arb.swap_pools) & set(arb_helper.swap_pools)
        ]
        # Drop conflicting arbs from working set.
        for arb in conflicting_arbs:
            all_profitable_arbs.remove(arb)
        if not all_profitable_arbs:
            break

    for arb_helper in arbs_without_overlap:
        arb_result = results_by_arb_id.get(arb_helper.id)
        if not arb_result:
            continue

        logger.info(
            f"Sending arb {arb_helper}, {arb_helper.id=}, backrunning {transaction_hash.hex()}. {time.perf_counter() - _start:.2f}s since start"
        )

        await send_to_builders(
            w3=w3,
            http_session=http_session,
            arb_result=arb_result,
            bot_status=bot_status,
            all_arbs=all_arbs,
            state_block=bot_status.current_block,
            target_block=bot_status.current_block + 1,
            tx_to_backrun=backrun_tx,  # Now using BackrunTx type
            backrun_set=backrun_hashes,
        ) 