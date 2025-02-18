"""
Module: tracker.py
Contains tracking functions such as track_balance and watchdog.
"""

import asyncio
import logging
from typing import Dict, Any
import degenbot
from degenbot.erc20 import Erc20Token
from .config import WETH_ADDRESS, EXECUTOR_CONTRACT_ADDRESS, OPERATOR_ADDRESS
from .types import BotStatus
from web3 import Web3

logger = logging.getLogger(__name__)

async def track_balance(
    w3: Web3,
    bot_status: BotStatus,
    all_arbs: dict
) -> None:
    """Track balances with proper typing"""
    weth = Erc20Token(WETH_ADDRESS)

    while True:
        await asyncio.sleep(bot_status.average_blocktime)
        try:
            executor_weth_balance = weth.get_balance(EXECUTOR_CONTRACT_ADDRESS)
            operator_eth_balance = w3.eth.get_balance(OPERATOR_ADDRESS)
        except asyncio.exceptions.CancelledError:
            return
        except Exception:
            continue
        else:
            updated_contract = bot_status.executor_balance != executor_weth_balance
            updated_operator = bot_status.operator_balance != operator_eth_balance

            if not updated_contract and not updated_operator:
                continue

            old_executor_balance = bot_status.executor_balance
            old_operator_balance = bot_status.operator_balance
            net_balance_change = (executor_weth_balance - old_executor_balance) - (old_operator_balance - operator_eth_balance)

            if updated_contract:
                bot_status.executor_balance = executor_weth_balance
                logger.info(f"Executor balance :  {executor_weth_balance/(10**18):.4f} WETH")
                for arb in all_arbs.values():
                    arb.max_input = executor_weth_balance
            if updated_operator:
                bot_status.operator_balance = operator_eth_balance
                logger.info(f"Operator balance :  {operator_eth_balance/(10**18):.4f} ETH")
            if old_executor_balance != 0 or old_operator_balance != 0:
                logger.info(f'Net              : {"" if net_balance_change < 0 else "+"}{net_balance_change/(10**18):.4f} ETH')

async def watchdog(bot_status: Any):  # Replace with your BotStatus type
    """
    Simple watchdog function.
    """
    while True:
        await asyncio.sleep(60)  # Check every minute
        logger.info("Watchdog check: system is alive.") 