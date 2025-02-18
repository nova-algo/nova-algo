"""
Module: builders.py
Contains the send_to_builders function responsible for forking the chain,
simulating transactions, generating payloads, building and signing transactions.
"""

import time
import web3
from web3.types import TxParams
from typing import Dict, Set, Optional, Any, Tuple, List
from hexbytes import HexBytes
import aiohttp
import logging
from degenbot.arbitrage import ArbitrageCalculationResult, UniswapCurveCycle
from degenbot.anvil import AnvilFork  # adjust the import based on your package structure
# Assumed helper functions – you might need to adjust their imports:
from degenbot.tx_helper import build_tx, sign_tx, simulate_bundle, _get_access_list
from .types import BotStatus, BackrunTx
from .simulation import simulate_bundle
from degenbot import AnvilFork

# Constants imported from the config module
from .config import NODE_HTTP_URI, EXECUTOR_CONTRACT_ADDRESS, OPERATOR_ADDRESS, GAS_FEE_MULTIPLIER

logger = logging.getLogger(__name__)

async def send_to_builders(
    w3: web3.Web3,
    http_session: aiohttp.ClientSession,
    arb_result: ArbitrageCalculationResult,
    bot_status: BotStatus,
    all_arbs: Dict[str, UniswapCurveCycle],
    state_block: int,
    target_block: int,
    tx_to_backrun: BackrunTx,
    backrun_set: Set,
) -> Optional[bool]:
    """
    Fork the chain, simulate, generate payloads, build and send the backrun transactions.
    Original inline comments have been preserved.
    """
    # If target block is already reached, abort.
    if target_block <= bot_status.current_block:
        return False

    try:
        arb_helper = all_arbs[arb_result.id]
    except KeyError:
        return False

    # fork and execute the backrun TX
    try:
        #  simulator = AnvilFork(
        #     fork_url=NODE_HTTP_URI,
        #     fork_block=state_block,
        #     chain_id=bot_status.chain_id,
        #     base_fee=bot_status.base_fee_next,
        #     balance_overrides=[
        #         (OPERATOR_ADDRESS, 100 * 10**18),
        #     ],
        # )
        simulator = AnvilFork(w3, state_block)
        simulator.w3.eth.send_raw_transaction(tx_to_backrun.raw)
    except Exception as exc:
        logger.info(f"eth_call reverted for mempool tx: {exc}")
        return

    tx_params = TxParams(
        **{
            "from": OPERATOR_ADDRESS,
            "chainId": bot_status.chain_id,
            "nonce": w3.eth.get_transaction_count(OPERATOR_ADDRESS),
            "maxFeePerGas": int(
                GAS_FEE_MULTIPLIER * max(bot_status.base_fee_next, bot_status.base_fee)
            ),
            "maxPriorityFeePerGas": 0,
            "value": 1,
        }
    )

    try:
        # Generate arbitrage payloads and build transaction.
        arbitrage_payloads = arb_helper.generate_payloads(
            from_address=EXECUTOR_CONTRACT_ADDRESS,
            swap_amount=arb_result.input_amount,
            pool_swap_amounts=arb_result.swap_amounts,
        )
        arbitrage_transaction = build_tx(
            payloads=arbitrage_payloads,
            tx_params=tx_params,
            w3=simulator.w3,
            balance_check=True,
        )
        arbitrage_transaction_raw = sign_tx(arbitrage_transaction)
    except web3.exceptions.ContractLogicError:
        # discard if the arb would revert
        return
    except Exception:
        logger.exception("(send_to_builders): generate_payloads, build_tx, sign_tx")
        return

    bundled_tx = (
        tx_to_backrun,
        arbitrage_transaction_raw,
        arbitrage_transaction,
    )

    simulator.reset(block_number=state_block)
    assert simulator.w3.eth.block_number == state_block, (
        f"Simulator block height ({simulator.w3.eth.block_number}) not at expected block height ({state_block})"
    )

    gas_use_with_access_list = None
    gas_use_without_access_list = None

    # Simulate bundle without access list.
    try:
        success, receipts = await simulate_bundle(
            bundle=bundled_tx,
            simulator=simulator,
            pre_check=True
        )
    except Exception as e:
        print(f"(simulate_bundle) (1): {e}")
        return False
    else:
        for i, result in enumerate(success):
            if result is False:
                # logger.info(f"Failure for TX {i} (1): {receipts[i]}")
                logger.info(f"Failure for TX {i} (1)")
        if False in success:
            arb_helper.swap_pools[1].auto_update()
            return False
        if hasattr(__import__("typing"), "TYPE_CHECKING"):
            assert receipts[1] is not None
        gas_use_without_access_list = receipts[1]["gasUsed"]

    simulator.reset(block_number=state_block)
    assert simulator.w3.eth.block_number == state_block, (
        f"Simulator block height ({simulator.w3.eth.block_number}) not at expected block height ({state_block})"
    )

    final_tx_params: Dict[str, Any] = dict(**arbitrage_transaction)
    # Will hold tuple: (BackrunTx, HexBytes, Dict[str, Any])
    final_tx_bundle: Tuple[Any, HexBytes, Dict[str, Any]] = None

    access_list: Optional[List] = _get_access_list(
        bundle=bundled_tx,
        arbitrage_transaction=arbitrage_transaction,
    )

    if access_list is not None:
        access_list = [
            entry
            for entry in access_list
            if entry["address"] != "0x0000000000000000000000000000000000000000"  # ZERO_ADDRESS
        ]

        try:
            # Add the access list and test for gas.
            final_tx_params["accessList"] = access_list
            arbitrage_transaction_raw_with_access_list = sign_tx(final_tx_params)
            final_tx_bundle = (
                tx_to_backrun,
                arbitrage_transaction_raw_with_access_list,
                final_tx_params,
            )
            success, receipts = await simulate_bundle(
                bundle=final_tx_bundle,
                simulator=simulator,
                pre_check=True
            )
        except Exception as e:
            print(f"(simulate_bundle) (2): {e}")
            return False
        else:
            for i, result in enumerate(success):
                if result is False:
                    logger.debug(f"Failure for TX {i} (2): {receipts[i]}")
            if False in success:
                return False
            else:
                if hasattr(__import__("typing"), "TYPE_CHECKING"):
                    assert receipts[1] is not None
                gas_use_with_access_list = receipts[1]["gasUsed"]

    simulator.reset(block_number=state_block)
    assert simulator.w3.eth.block_number == state_block, (
        f"Simulator block height ({simulator.w3.eth.block_number}) not at expected block height ({state_block})"
    )

    if (
        access_list is not None
        and gas_use_with_access_list is not None
        and gas_use_with_access_list < gas_use_without_access_list
    ):
        # Include the access list and update the estimate if the access
        # list provides gas savings compared to the "vanilla" TX.
        arb_helper.gas_estimate = gas_use_with_access_list
        final_tx_params["accessList"] = access_list
        logger.info(f"Added access list: {gas_use_without_access_list - gas_use_with_access_list} gas reduction")
    else:
        final_tx_params.pop("accessList", None)

    if hasattr(__import__("typing"), "TYPE_CHECKING"):
        assert bot_status.base_fee_next is not None

    gas_fee = arb_helper.gas_estimate * bot_status.base_fee_next
    arb_net_profit = arb_result.profit_amount - gas_fee

    logger.info(f"Arb     :  {arb_helper}")
    logger.info(f"Backrun :  {tx_to_backrun.hash.hex()}")

    # Return final transaction bundle or further process it.
    return final_tx_bundle 