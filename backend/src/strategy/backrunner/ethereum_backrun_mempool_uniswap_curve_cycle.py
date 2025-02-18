import asyncio
import dataclasses
import functools
import logging
import multiprocessing
import signal
import sys
import threading
import time
from collections import deque
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Deque,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    TypedDict,
    Union,
)

import aiohttp
import degenbot
import degenbot.exceptions
import dotenv
import eth_abi.abi  # type: ignore[import-untyped]
import eth_account.datastructures
import eth_account.messages
import ujson
import web3
import web3.exceptions
import websockets.exceptions
from degenbot import AnvilFork
from degenbot.arbitrage import (
    ArbitrageCalculationResult,
    UniswapCurveCycle,
)
from degenbot.constants import ZERO_ADDRESS
from degenbot.uniswap import (
    UniswapV3LiquiditySnapshot,
    UniswapV3PoolExternalUpdate,
)
from degenbot.uniswap.abi import (
    UNISWAP_UNIVERSAL_ROUTER2_ABI,
    UNISWAP_UNIVERSAL_ROUTER3_ABI,
    UNISWAP_UNIVERSAL_ROUTER_ABI,
    UNISWAP_V2_ROUTER2_ABI,
    UNISWAP_V2_ROUTER_ABI,
    UNISWAP_V3_ROUTER2_ABI,
    UNISWAP_V3_ROUTER_ABI,
)
from eth_typing import ChecksumAddress
from eth_utils import to_checksum_address
from hexbytes import HexBytes
from web3.types import RPCResponse, TxParams, TxReceipt


CONFIG: Dict[str, Any] = dotenv.dotenv_values("mainnet_full.env")
OPERATOR_ADDRESS = to_checksum_address(CONFIG["OPERATOR_ADDRESS"])
EXECUTOR_CONTRACT_ADDRESS = to_checksum_address(
    CONFIG["EXECUTOR_CONTRACT_ADDRESS"]
)
EXECUTOR_CONTRACT_ABI = CONFIG["EXECUTOR_CONTRACT_ABI"]
NODE_HTTP_URI = (
    CONFIG["NODE_HOST_HTTP"] + ":" + CONFIG["NODE_PORT_HTTP"]
)
NODE_WEBSOCKET_URI = (
    CONFIG["NODE_HOST_WEBSOCKET"] + ":" + CONFIG["NODE_PORT_WEBSOCKET"]
)
NODE_IPC_PATH = CONFIG["NODE_IPC_PATH"]
WETH_ADDRESS = to_checksum_address(CONFIG["WRAPPED_TOKEN_ADDRESS"])

MIN_PROFIT_GROSS = int(
    0.0005 * 10**18
)  # first filter for gross arb profit (excludes gas)
MIN_PROFIT_NET = int(
    0.000005 * 10**18
)  # second filter for net arb profit (includes gas)

SUBSCRIBE_TO_FULL_TRANSACTIONS = True
EVENT_PROCESS_DELAY = 0.1

BRIBE = 0.95  # % of net profit to bribe the builder
BRIBE_BIPS = int(10_000 * BRIBE)

GAS_FEE_MULTIPLIER = 1.25
BUNDLE_VALID_BLOCKS = 3

ROUTERS: Dict[ChecksumAddress, Dict[str, Any]]

VERBOSE_BLOCKS = True
VERBOSE_PROCESSING = False
VERBOSE_UPDATES = False
VERBOSE_WATCHDOG = True
VERBOSE_BUNDLE_RESULTS = True

AVERAGE_BLOCK_TIME = 12.0
LATE_BLOCK_THRESHOLD = 6.0

DEBUG = True
DRY_RUN = True

BUILDERS = [
    "https://rpc.titanbuilder.xyz",
    "https://builder0x69.io",
    "https://rpc.beaverbuild.org",
    "https://rsync-builder.xyz",
    "https://relay.flashbots.net",
]


@dataclasses.dataclass
class BackrunTx:
    tx: Dict
    raw: HexBytes
    hash: HexBytes


@dataclasses.dataclass
class BotStatus:
    current_block: int
    current_block_timestamp: int
    chain_id: int
    base_fee: int
    base_fee_next: int
    live: bool = False
    first_block: int = 0
    first_event: int = 0
    watching_blocks: bool = False
    watching_events: bool = False
    executor_balance: int = 0
    average_blocktime: float = AVERAGE_BLOCK_TIME
    paused: bool = False
    operator_balance: int = 0
    processing_tx: bool = False
    number_of_tx_processing: int = 0


def _pool_worker_init():
    """
    Ignore SIGINT signals. Used for subprocesses spawned by `ProcessPoolExecutor` via the `initializer=` argument.

    Otherwise SIGINT is translated to KeyboardInterrupt, which is unhandled and will lead to messy tracebacks when thrown into a subprocess.
    """
    signal.signal(signal.SIGINT, signal.SIG_IGN)


async def main() -> None:
    # Create a reusable web3 object to communicate with the node
    # node_w3 = web3.Web3(web3.HTTPProvider(NODE_HTTP_URI))
    # node_w3 = web3.Web3(web3.WebsocketProvider(NODE_WEBSOCKET_URI))
    node_w3 = web3.Web3(web3.IPCProvider(NODE_IPC_PATH))

    global ROUTERS
    ROUTERS = {
        to_checksum_address(
            "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F"
        ): {
            "name": "Sushiswap",
            "abi": UNISWAP_V2_ROUTER_ABI,
        },
        to_checksum_address(
            "0xf164fC0Ec4E93095b804a4795bBe1e041497b92a"
        ): {
            "name": "UniswapV2: Router",
            "abi": UNISWAP_V2_ROUTER_ABI,
        },
        to_checksum_address(
            "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
        ): {
            "name": "UniswapV2: Router 2",
            "abi": UNISWAP_V2_ROUTER2_ABI,
        },
        to_checksum_address(
            "0xE592427A0AEce92De3Edee1F18E0157C05861564"
        ): {
            "name": "UniswapV3: Router",
            "abi": UNISWAP_V3_ROUTER_ABI,
        },
        to_checksum_address(
            "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45"
        ): {
            "name": "UniswapV3: Router 2",
            "abi": UNISWAP_V3_ROUTER2_ABI,
        },
        to_checksum_address(
            "0xEf1c6E67703c7BD7107eed8303Fbe6EC2554BF6B"
        ): {
            "name": "Uniswap Universal Router",
            "abi": UNISWAP_UNIVERSAL_ROUTER_ABI,
        },
        to_checksum_address(
            "0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD"
        ): {
            "name": "Uniswap Universal Router (V1_2)",
            "abi": UNISWAP_UNIVERSAL_ROUTER2_ABI,
        },
        to_checksum_address(
            "0x3F6328669a86bef431Dc6F9201A5B90F7975a023"
        ): {
            "name": "Uniswap Universal Router (V1_3)",
            "abi": UNISWAP_UNIVERSAL_ROUTER3_ABI,
        },
    }

    degenbot.set_web3(node_w3)

    current_block = node_w3.eth.get_block("latest")

    bot_status = BotStatus(
        chain_id=node_w3.eth.chain_id,
        base_fee=current_block["baseFeePerGas"],
        base_fee_next=degenbot.next_base_fee(
            parent_base_fee=current_block["baseFeePerGas"],
            parent_gas_used=current_block["gasUsed"],
            parent_gas_limit=current_block["gasLimit"],
        ),
        current_block=current_block["number"],
        current_block_timestamp=current_block["timestamp"],
    )

    all_arbs: Dict[str, UniswapCurveCycle] = dict()
    all_backrun_hashes: Set[str] = set()
    all_pools = degenbot.AllPools(bot_status.chain_id)
    all_tasks: Set[asyncio.Task] = set()
    events: Deque[RPCResponse] = deque()

    pending_tx: Dict[HexBytes, dict | None] = dict()
    pool_managers: Dict[
        str,
        Union[
            degenbot.UniswapV2LiquidityPoolManager,
            degenbot.UniswapV3LiquidityPoolManager,
        ],
    ] = dict()

    snapshot = UniswapV3LiquiditySnapshot(
        file="ethereum_v3_liquidity_snapshot.json"
    )

    shutdown_event = threading.Event()

    signals = (
        signal.SIGHUP,
        signal.SIGTERM,
        signal.SIGINT,
        # signal.SIGBREAK, # For Windows users, will catch CTRL+C
    )
    for sig in signals:
        asyncio.get_event_loop().add_signal_handler(
            sig,
            shutdown,
            all_tasks,
            shutdown_event,
        )

    def _handle_task_exception(*args):
        """
        This handler is the "catcher of last resort" for tasks.
        If an exception is not handled and the task is garbage collected, it will end up here.
        If these are not handled (by this or by others) they will be printed at the termination of the event loop.
        """
        if DEBUG:
            for arg in args:
                print(arg)

    asyncio.get_running_loop().set_exception_handler(
        _handle_task_exception
    )

    with ProcessPoolExecutor(
        mp_context=multiprocessing.get_context("spawn"),
        initializer=_pool_worker_init,
        max_workers=8,
    ) as process_pool:
        with ThreadPoolExecutor() as thread_pool:
            asyncio.get_running_loop().run_in_executor(
                thread_pool,
                load_arbs,
                shutdown_event,
                all_pools,
                all_arbs,
                bot_status,
                snapshot,
                pool_managers,
            )

            async with aiohttp.ClientSession(
                raise_for_status=True
            ) as http_session:
                for coro in [
                    subscription_watcher(
                        bot_status=bot_status,
                        events=events,
                        pending_tx=pending_tx,
                        backrun_hashes=all_backrun_hashes,
                        w3=node_w3,
                        http_session=http_session,
                        process_pool=process_pool,
                        tasks=all_tasks,
                        all_arbs=all_arbs,
                    ),
                    track_balance(
                        w3=node_w3,
                        all_arbs=all_arbs,
                        bot_status=bot_status,
                    ),
                    process_events(
                        events=events,
                        bot_status=bot_status,
                        snapshot=snapshot,
                        pool_managers=pool_managers,
                        all_pools=all_pools,
                    ),
                    watchdog(
                        bot_status=bot_status,
                    ),
                ]:
                    task = asyncio.create_task(coro)
                    task.add_done_callback(all_tasks.discard)
                    all_tasks.add(task)

                try:
                    await asyncio.gather(*all_tasks)
                except asyncio.CancelledError:
                    pass
                except Exception:
                    logger.exception("(main) catch-all")


async def send_to_builders(
    w3: web3.Web3,
    http_session: aiohttp.ClientSession,
    arb_result: ArbitrageCalculationResult,
    bot_status: BotStatus,
    all_arbs: Dict[str, UniswapCurveCycle],
    state_block: int,
    target_block: int,
    backrun_set: Set,
    tx_to_backrun: BackrunTx,
):
    def build_tx(
        payloads: List[Tuple[ChecksumAddress, bytes, int]],
        tx_params: TxParams,
        w3: web3.Web3,
        balance_check: bool = True,
    ) -> TxParams:
        return (
            w3.eth.contract(
                address=EXECUTOR_CONTRACT_ADDRESS,
                abi=EXECUTOR_CONTRACT_ABI,
            )
            .functions.execute_payloads(
                payloads=payloads,
                balance_check=balance_check,
                bribe_bips=BRIBE_BIPS,
            )
            .build_transaction(transaction=tx_params)
        )

    def _get_access_list(
        bundle: Tuple[BackrunTx, HexBytes, TxParams],
        arbitrage_transaction: TxParams,
    ) -> list | None:
        anvil_fork = AnvilFork(
            fork_url=NODE_HTTP_URI,
            fork_block=state_block,
            chain_id=bot_status.chain_id,
            base_fee=bot_status.base_fee_next,
            balance_overrides=[
                (OPERATOR_ADDRESS, 100 * 10**18),
            ],
        )
        fork_w3 = anvil_fork.w3

        mempool_tx, *_ = bundle

        try:
            mempool_tx_hash = fork_w3.eth.send_raw_transaction(
                mempool_tx.raw
            )
            mempool_tx_receipt = (
                fork_w3.eth.wait_for_transaction_receipt(
                    mempool_tx_hash, timeout=0.25
                )
            )
        except Exception as e:
            print(f"(get_access_list.send_transaction): {e}")
            return None
        else:
            # 'status' = 0 for reverts, 1 for success
            if mempool_tx_receipt["status"] == 0:
                logger.info(f"{mempool_tx_receipt=}")

        try:
            return anvil_fork.create_access_list(
                {
                    "from": arbitrage_transaction["from"],
                    "to": arbitrage_transaction["to"],
                    "data": arbitrage_transaction["data"],
                    # "gas": hex(
                    #     int(1.25 * arbitrage_transaction["gas"])
                    # ),
                }
            )
        except Exception:
            logger.exception("(get_access_list.create_access_list)")
            raise

    async def send_bundle_to_builder(
        bundle: Iterable[HexBytes],
        builder_url: str,
        blocks: Iterable[int],
    ) -> Tuple[str, list]:
        results = []
        formatted_bundle: List[str] = [tx.hex() for tx in bundle]

        for block in blocks:
            send_bundle_payload = ujson.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "eth_sendBundle",
                    "params": [
                        {
                            "txs": formatted_bundle,  # Array[String], a list of signed transactions to execute in an atomic bundle
                            "blockNumber": hex(
                                block
                            ),  # String, a hex encoded block number for which this bundle is valid on
                        }
                    ],
                }
            )

            send_bundle_message: (
                eth_account.datastructures.SignedMessage
            ) = eth_account.Account.sign_message(
                signable_message=eth_account.messages.encode_defunct(
                    text=web3.Web3.keccak(
                        text=send_bundle_payload
                    ).hex()
                ),
                private_key=CONFIG["BUNDLE_SIGNER_PRIVATE_KEY"],
            )
            send_bundle_signature = (
                CONFIG["BUNDLE_SIGNER_ADDRESS"]
                + ":"
                + send_bundle_message.signature.hex()
            )
            send_bundle_headers = {
                "Content-Type": "application/json",
                "X-Flashbots-Signature": send_bundle_signature,
                "X-Auction-Signature": send_bundle_signature,
            }

            try:
                async with http_session.post(
                    url=builder_url,
                    headers=send_bundle_headers,
                    data=send_bundle_payload,
                ) as resp:
                    relay_response = await resp.json(
                        content_type=None,  # some relays do not correctly set the MIME type for JSON data
                    )
            except aiohttp.ClientError as e:
                raise Exception(
                    f"(send_bundle) HTTP Error: {e}", builder_url
                ) from e
            else:
                await asyncio.sleep(
                    1.0
                )  # reduce potential for rate limiting
                results.append(relay_response["result"])

        return builder_url, results

    def sign_tx(tx: Dict[str, Any]) -> HexBytes:
        key: str = CONFIG["OPERATOR_PRIVATE_KEY"]
        acct: eth_account.Account = eth_account.Account.from_key(key)
        signed_tx: eth_account.datastructures.SignedTransaction = (
            acct.sign_transaction(transaction_dict=tx)
        )
        return signed_tx.rawTransaction

    async def simulate_bundle(
        bundle: Tuple[BackrunTx, HexBytes, TxParams | Dict[str, Any]],
        simulator: AnvilFork,
        pre_check=True,
    ) -> Tuple[List[bool], List[TxReceipt | None]]:
        """
        Execute the transaction bundle against the fork.

        Returns a tuple of success values and transaction receipts:
          - success: List[bool]
          - receipts: List[Dict]
        """

        mempool_tx, arb_tx_raw, arb_tx = bundle
        success: List[bool] = [False] * 2

        mempool_tx_receipt: Optional[TxReceipt] = None
        arb_tx_receipt: Optional[TxReceipt] = None

        try:
            mempool_tx_hash = simulator.w3.eth.send_raw_transaction(
                mempool_tx.raw
            )
            mempool_tx_receipt = (
                simulator.w3.eth.wait_for_transaction_receipt(
                    mempool_tx_hash, timeout=0.25
                )
            )
        except Exception as e:
            print(f"(simulate_bundle.send_transaction): {e}")
            raise
        else:
            if TYPE_CHECKING:
                assert mempool_tx_receipt is not None
            # 'status' = 0 for reverts, 1 for success
            if mempool_tx_receipt["status"] == 1:
                success[0] = True

        if pre_check:
            try:
                simulator.w3.eth.call(arb_tx)
            except Exception as e:
                print(f"eth_call failed for arb tx - {type(e)}: {e}")
                print(f"{arb_tx=}")

        try:
            arb_tx_hash = simulator.w3.eth.send_raw_transaction(
                arb_tx_raw
            )
            arb_tx_receipt = (
                simulator.w3.eth.wait_for_transaction_receipt(
                    arb_tx_hash, timeout=0.25
                )
            )
        except Exception as e:
            print(f"(send_raw_transaction): {e}")
            raise
        else:
            if TYPE_CHECKING:
                assert arb_tx_receipt is not None
            # 'status' = 0 for reverts, 1 for success
            if arb_tx_receipt["status"] == 1:
                success[1] = True

        return success, [mempool_tx_receipt, arb_tx_receipt]

    if target_block <= bot_status.current_block:
        return False

    try:
        arb_helper = all_arbs[arb_result.id]
    except KeyError:
        return False

    # fork and execute the backrun TX
    try:
        simulator = AnvilFork(
            fork_url=NODE_HTTP_URI,
            fork_block=state_block,
            chain_id=bot_status.chain_id,
            base_fee=bot_status.base_fee_next,
            balance_overrides=[
                (OPERATOR_ADDRESS, 100 * 10**18),
            ],
        )
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
                GAS_FEE_MULTIPLIER
                * max(bot_status.base_fee_next, bot_status.base_fee)
            ),
            "maxPriorityFeePerGas": 0,
            "value": 1,
        }
    )

    try:
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
        logger.exception(
            "(send_to_builders): generate_payloads, build_tx, sign_tx"
        )
        return

    bundled_tx = (
        tx_to_backrun,
        arbitrage_transaction_raw,
        arbitrage_transaction,
    )

    simulator.reset(block_number=state_block)
    assert (
        simulator.w3.eth.block_number == state_block
    ), f"Simulator block height ({simulator.w3.eth.block_number}) not at expected block height ({state_block})"

    gas_use_with_access_list = None
    gas_use_without_access_list = None

    try:
        successes, receipts = await simulate_bundle(
            bundle=bundled_tx,
            simulator=simulator,
        )
    except Exception as e:
        print(f"(simulate_bundle) (1): {e}")
        return False
    else:
        for i, result in enumerate(successes):
            if result is False:
                # logger.info(f"Failure for TX {i} (1): {receipts[i]}")
                logger.info(f"Failure for TX {i} (1)")

        if False in successes:
            arb_helper.swap_pools[1].auto_update()
            return False

        if TYPE_CHECKING:
            assert receipts[1] is not None

        gas_use_without_access_list = receipts[1]["gasUsed"]

    simulator.reset(block_number=state_block)
    assert (
        simulator.w3.eth.block_number == state_block
    ), f"Simulator block height ({simulator.w3.eth.block_number}) not at expected block height ({state_block})"

    final_tx_params: Dict[str, Any] = dict(**arbitrage_transaction)
    final_tx_bundle: Tuple[BackrunTx, HexBytes, Dict[str, Any]]

    access_list: Optional[List]
    access_list = _get_access_list(
        bundle=bundled_tx,
        arbitrage_transaction=arbitrage_transaction,
    )

    if access_list is not None:
        access_list = [
            entry
            for entry in access_list
            if entry["address"] != ZERO_ADDRESS
        ]

        try:
            # Add the access list and test for gas
            final_tx_params["accessList"] = access_list
            arbitrage_transaction_raw_with_access_list = sign_tx(
                final_tx_params
            )
            final_tx_bundle = (
                tx_to_backrun,
                arbitrage_transaction_raw_with_access_list,
                final_tx_params,
            )
            successes, receipts = await simulate_bundle(
                bundle=final_tx_bundle,
                simulator=simulator,
            )
        except Exception as e:
            print(f"(simulate_bundle) (2): {e}")
            return False
        else:
            for i, result in enumerate(successes):
                if result is False:
                    logger.debug(
                        f"Failure for TX {i} (2): {receipts[i]}"
                    )
            if False in successes:
                return False
            else:
                if TYPE_CHECKING:
                    assert receipts[1] is not None
                gas_use_with_access_list = receipts[1]["gasUsed"]

    simulator.reset(block_number=state_block)
    assert (
        simulator.w3.eth.block_number == state_block
    ), f"Simulator block height ({simulator.w3.eth.block_number}) not at expected block height ({state_block})"

    if (
        access_list is not None
        and gas_use_with_access_list is not None
        and gas_use_with_access_list < gas_use_without_access_list
    ):
        # Include the access list and update the estimate if the access
        # list provides gas savings compared to the "vanilla" TX
        arb_helper.gas_estimate = gas_use_with_access_list
        final_tx_params["accessList"] = access_list
        logger.info(
            f"Added access list: {gas_use_without_access_list - gas_use_with_access_list} gas reduction"
        )
    else:
        final_tx_params.pop("accessList")

    if TYPE_CHECKING:
        assert bot_status.base_fee_next is not None

    gas_fee = arb_helper.gas_estimate * bot_status.base_fee_next
    arb_net_profit = arb_result.profit_amount - gas_fee

    logger.info(f"Arb     :  {arb_helper}")
    logger.info(f"Backrun :  {tx_to_backrun.hash.hex()}")
    logger.info(
        f"Input   :  {arb_result.input_amount / 10**(arb_result.input_token.decimals):0.5f} {arb_result.input_token}"
    )
    logger.info(
        f"Profit  :  {arb_result.profit_amount/(10**arb_result.profit_token.decimals):0.5f} ETH"
    )
    logger.info(
        f"Gas Fee :  {gas_fee/(10**18):0.5f} ETH ({arb_helper.gas_estimate} gas estimate)"
    )
    logger.info(
        f'Net     : {"" if arb_net_profit < 0 else "+"}{arb_net_profit/(10**18):0.5f} ETH'
    )

    if arb_net_profit < MIN_PROFIT_NET:
        return False

    bribe = max(0, int(BRIBE * arb_net_profit))
    # bribe_gas = bribe // arb_helper.gas_estimate

    logger.info(f"Bribe   :  {bribe/(10**18):0.5f} ETH")
    logger.info("*** EXECUTING BACKRUN ARB (RELAY) ***")

    # Update the arbitrage transaction with the final bribe
    final_tx_params["value"] = bribe

    arbitrage_transaction_final_raw = sign_tx(final_tx_params)

    final_bundle: Tuple[HexBytes, HexBytes]
    final_bundle = (
        tx_to_backrun.raw,
        arbitrage_transaction_final_raw,
    )

    if DRY_RUN:
        logger.info("RELAY SUBMISSION CANCELLED (DRY RUN ACTIVE)")
        return False

    submitted_blocks = set()
    backrun_set.add(tx_to_backrun.hash)
    tasks = [
        send_bundle_to_builder(
            bundle=final_bundle,
            builder_url=builder_url,
            blocks=range(
                target_block,
                target_block + BUNDLE_VALID_BLOCKS,
            ),
        )
        for builder_url in BUILDERS
    ]

    for i in range(BUNDLE_VALID_BLOCKS):
        submitted_blocks.add(target_block + i)
    logger.info(
        f"Bundles sent for blocks {target_block}-{target_block + BUNDLE_VALID_BLOCKS - 1}"
    )

    for task in asyncio.as_completed(tasks):
        try:
            builder, bundle_result = await task
        except Exception as e:
            builder = e.args[1]
            logger.info(f"Bundle error from {builder}: {e}")
        else:
            if VERBOSE_BUNDLE_RESULTS:
                logger.info(
                    f"Bundle result from {builder}: {bundle_result}"
                )

    return True


def load_arbs(
    shutdown_event: threading.Event,
    all_pools: degenbot.AllPools,
    all_arbs: Dict[str, UniswapCurveCycle],
    bot_status: BotStatus,
    snapshot: UniswapV3LiquiditySnapshot,
    pool_managers: Dict[
        str,
        Union[
            degenbot.UniswapV2LiquidityPoolManager,
            degenbot.UniswapV3LiquidityPoolManager,
        ],
    ],
):
    logger.info("Starting arb loading function")

    while not bot_status.first_event:
        time.sleep(1)
        if shutdown_event.is_set():
            return

    # Update to the block BEFORE the event watcher came online
    snapshot.fetch_new_liquidity_events(bot_status.first_event - 1)

    # Uniswap V2
    univ2_lp_manager = degenbot.UniswapV2LiquidityPoolManager(
        factory_address="0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
    )
    pool_managers[
        "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
    ] = univ2_lp_manager

    # Uniswap V3
    univ3_lp_manager = degenbot.UniswapV3LiquidityPoolManager(
        factory_address="0x1F98431c8aD98523631AE4a59f267346ea31F984",
        snapshot=snapshot,
    )
    pool_managers[
        "0x1F98431c8aD98523631AE4a59f267346ea31F984"
    ] = univ3_lp_manager

    # Sushiswap V2
    sushiv2_lp_manager = degenbot.UniswapV2LiquidityPoolManager(
        factory_address="0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac"
    )
    pool_managers[
        "0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac"
    ] = sushiv2_lp_manager

    # Sushiswap V3
    sushiv3_lp_manager = degenbot.UniswapV3LiquidityPoolManager(
        factory_address="0xbACEB8eC6b9355Dfc0269C18bac9d6E2Bdc29C4F",
        snapshot=snapshot,
    )
    pool_managers[
        "0xbACEB8eC6b9355Dfc0269C18bac9d6E2Bdc29C4F"
    ] = sushiv3_lp_manager

    liquidity_pool_data = {}
    for liquidity_pool_filename in [
        "ethereum_lps_sushiswapv2.json",
        "ethereum_lps_sushiswapv3.json",
        "ethereum_lps_uniswapv2.json",
        "ethereum_lps_uniswapv3.json",
        "ethereum_lps_curvev1_factory.json",
        "ethereum_lps_curvev1_registry.json",
    ]:
        with open(liquidity_pool_filename, encoding="utf-8") as file:
            valid = True
            pool: Dict[str, Any]
            for pool in ujson.load(file):
                if pool.get("pool_address") is None:
                    continue
                if pool["pool_address"] in BLACKLISTED_POOLS:
                    valid = False
                if "token0" in pool:
                    if (
                        pool["token0"] in BLACKLISTED_TOKENS
                        or pool["token1"] in BLACKLISTED_TOKENS
                    ):
                        valid = False
                if "coin_addresses" in pool:
                    for coin_address in pool["coin_addresses"]:
                        if coin_address in BLACKLISTED_TOKENS:
                            valid = False
                if "underlying_coin_addresses" in pool:
                    for coin_address in pool[
                        "underlying_coin_addresses"
                    ]:
                        if coin_address in BLACKLISTED_TOKENS:
                            valid = False

                if valid:
                    liquidity_pool_data[pool["pool_address"]] = pool
                else:
                    continue
    logger.info(f"Found {len(liquidity_pool_data)} pools")

    arb_paths = []
    for arb_filename in [
        "ethereum_arbs_3pool_curve.json",
    ]:
        with open(arb_filename, encoding="utf-8") as file:
            for arb_id, arb in ujson.load(file).items():
                passed_checks = True
                if arb_id in BLACKLISTED_ARBS:
                    passed_checks = False
                for pool_address in arb["path"]:
                    if not liquidity_pool_data.get(pool_address):
                        passed_checks = False
                        break
                if passed_checks:
                    arb_paths.append(arb)
    logger.info(f"Found {len(arb_paths)} arb paths")

    # Identify all unique pool addresses in arb paths
    unique_pool_addresses = {
        pool_address
        for arb in arb_paths
        for pool_address in arb["path"]
        if liquidity_pool_data.get(pool_address)
    }
    logger.info(f"Found {len(unique_pool_addresses)} unique pools")

    start_time = time.perf_counter()

    for pool_address in unique_pool_addresses:
        if shutdown_event.is_set():
            return

        pool_type: str = liquidity_pool_data[pool_address]["type"]

        pool_helper: Optional[
            Union[
                degenbot.LiquidityPool,
                degenbot.V3LiquidityPool,
                degenbot.CurveStableswapPool,
            ]
        ] = None

        if pool_type == "UniswapV2":
            try:
                pool_helper = univ2_lp_manager.get_pool(
                    pool_address=pool_address,
                    silent=True,
                    update_method="external",
                    state_block=bot_status.first_event - 1,
                )
            except degenbot.exceptions.ManagerError as exc:
                print(f"UniswapV2 get_pool: {exc}")
                continue

        elif pool_type == "SushiswapV2":
            try:
                pool_helper = sushiv2_lp_manager.get_pool(
                    pool_address=pool_address,
                    silent=True,
                    update_method="external",
                    state_block=bot_status.first_event - 1,
                )
            except degenbot.exceptions.ManagerError as exc:
                print(f"SushiswapV2 get_pool: {exc}")
                continue

        elif pool_type == "UniswapV3":
            try:
                pool_helper = univ3_lp_manager.get_pool(
                    pool_address=pool_address,
                    silent=True,
                    state_block=bot_status.first_event - 1,
                    v3liquiditypool_kwargs={
                        "fee": liquidity_pool_data[pool_address]["fee"]
                    },
                )
            except degenbot.exceptions.ManagerError as exc:
                print(f"UniswapV3 get_pool: {exc}")
                continue

        elif pool_type == "SushiswapV3":
            try:
                pool_helper = sushiv3_lp_manager.get_pool(
                    pool_address=pool_address,
                    silent=True,
                    state_block=bot_status.first_event - 1,
                    v3liquiditypool_kwargs={
                        "fee": liquidity_pool_data[pool_address]["fee"]
                    },
                )
            except degenbot.exceptions.ManagerError as exc:
                print(f"SushiswapV3 get_pool: {exc}")
                continue

        elif pool_type == "CurveV1":
            try:
                pool_helper = degenbot.CurveStableswapPool(
                    address=pool_address,
                    silent=True,
                    state_block=bot_status.first_event - 1,
                )
            except Exception as exc:
                print(f"CurveV1 get_pool: {type(exc)}: {exc}")
                continue

        else:
            raise Exception(
                f"Could not identify pool type! {pool_type=}"
            )

        if TYPE_CHECKING:
            assert isinstance(
                pool_helper,
                (
                    degenbot.CurveStableswapPool,
                    degenbot.LiquidityPool,
                    degenbot.V3LiquidityPool,
                ),
            )

        if snapshot and isinstance(
            pool_helper, degenbot.V3LiquidityPool
        ):
            assert pool_helper._sparse_bitmap is False

    logger.info(
        f"Created {len(all_pools)} liquidity pool helpers in {time.perf_counter() - start_time:.2f}s"
    )

    degenbot_erc20token_weth = degenbot.Erc20Token(WETH_ADDRESS)

    for arb in arb_paths:
        if shutdown_event.is_set():
            return

        # Ignore arbs on the blacklist
        if (arb_id := arb.get("id")) in BLACKLISTED_ARBS:
            continue

        # Ignore arbs where pool helpers are not available for all pools in the path
        if len(
            swap_pools := [
                pool_obj
                for pool_address in arb["path"]
                if (pool_obj := all_pools.get(pool_address))
            ]
        ) != len(arb["path"]):
            continue

        # determine whether the arb should be all-Uniswap or Uniswap-Curve-Uniswap
        match len(swap_pools):
            case 3:
                match swap_pools[1]:
                    case degenbot.CurveStableswapPool():
                        try:
                            arb = UniswapCurveCycle(
                                input_token=degenbot_erc20token_weth,
                                swap_pools=swap_pools,
                                id=arb_id,
                                max_input=bot_status.executor_balance,
                            )
                        except ValueError:
                            # TODO: remove this TERRIBLE hack after Curve arb helper supports swapping LP token
                            pass
                        else:
                            assert arb._swap_vectors
                            all_arbs[arb.id] = arb
                    case _:
                        pass

            case _:
                raise Exception("Uh oh!")

        # logger.info(f"Added {all_arbs[arb_id]}")

    bot_status.live = True
    logger.info(f"Built {len(all_arbs)} cycle arb helpers")
    logger.info("Arb loading complete")


def shutdown(tasks: Set[asyncio.Task], shutdown_event: threading.Event):
    """
    Cancel all tasks in the `tasks` set and set the shutdown event for threads
    """

    shutdown_event.set()

    logger.info("Cancelling tasks")
    for task in tasks:
        task.cancel()


async def track_balance(
    w3: web3.Web3,
    all_arbs: Dict[str, UniswapCurveCycle],
    bot_status: BotStatus,
):
    weth = degenbot.Erc20Token(WETH_ADDRESS)

    while True:
        await asyncio.sleep(bot_status.average_blocktime)
        try:
            executor_weth_balance = weth.get_balance(
                EXECUTOR_CONTRACT_ADDRESS
            )
            operator_eth_balance = w3.eth.get_balance(OPERATOR_ADDRESS)
        except asyncio.exceptions.CancelledError:
            return
        except Exception:
            continue
        else:
            updated_contract: bool = (
                bot_status.executor_balance != executor_weth_balance
            )
            updated_operator: bool = (
                bot_status.operator_balance != operator_eth_balance
            )

            if not updated_contract and not updated_operator:
                continue

            old_executor_balance = bot_status.executor_balance
            old_operator_balance = bot_status.operator_balance
            net_balance_change = (
                executor_weth_balance - old_executor_balance
            ) - (old_operator_balance - operator_eth_balance)

            if updated_contract or updated_operator:
                print()

            if updated_contract:
                bot_status.executor_balance = executor_weth_balance
                logger.info(
                    f"Executor balance :  {executor_weth_balance/(10**18):.4f} WETH"
                )
                for arb in all_arbs.values():
                    arb.max_input = executor_weth_balance

            if updated_operator:
                bot_status.operator_balance = operator_eth_balance
                logger.info(
                    f"Operator balance :  {operator_eth_balance/(10**18):.4f} ETH"
                )

            if old_executor_balance != 0 or old_operator_balance != 0:
                logger.info(
                    f'Net              : {"" if net_balance_change < 0 else "+"}{net_balance_change/(10**18):.4f} ETH'
                )

            if updated_contract or updated_operator:
                print()


async def watchdog(bot_status: BotStatus):
    """
    Monitor other coroutines, functions, objects, etc. and set bot status
    variables.

    Other coroutines should monitor the state of `bot_status.paused` and
    adjust their activity as needed
    """

    logger.info("Starting status watchdog")

    while True:
        try:
            await asyncio.sleep(1)
            time_since_last_block = (
                time.time() - bot_status.current_block_timestamp
            )

            # System clock will always be ahead of the last block timestamp,
            # but an excessive delay indicates a network issue
            if (
                time_since_last_block
                > bot_status.average_blocktime + LATE_BLOCK_THRESHOLD
            ):
                if not bot_status.paused:
                    bot_status.paused = True
                    if VERBOSE_WATCHDOG:
                        logger.info(
                            f"WATCHDOG: paused (block {time_since_last_block - bot_status.average_blocktime:.1f}s late)"
                        )
            else:
                if bot_status.paused:
                    bot_status.paused = False
                    if VERBOSE_WATCHDOG:
                        logger.info("WATCHDOG: unpaused")

        except asyncio.exceptions.CancelledError:
            return


async def process_events(
    events: Deque[RPCResponse],
    bot_status: BotStatus,
    snapshot: UniswapV3LiquiditySnapshot,
    pool_managers: Dict[
        str,
        Union[
            degenbot.UniswapV2LiquidityPoolManager,
            degenbot.UniswapV3LiquidityPoolManager,
        ],
    ],
    all_pools: degenbot.AllPools,
):
    def process_burn_event(message: dict, removed: bool = False):
        # Specification per https://github.com/Uniswap/v3-core/blob/main/contracts/interfaces/pool/IUniswapV3PoolEvents.sol#L55
        # event Burn(
        #     address indexed owner,
        #     int24 indexed tickLower,
        #     int24 indexed tickUpper,
        #     uint128 amount,
        #     uint256 amount0,
        #     uint256 amount1
        # );
        event_address = to_checksum_address(
            message["result"]["address"]
        )
        event_block = message["result"]["blockNumber"]
        if not isinstance(event_block, int):
            event_block = int.from_bytes(event_block)
        event_data = message["result"]["data"]

        v3_pool_helper: Optional[degenbot.V3LiquidityPool] = None
        v3_pool_manager: degenbot.UniswapV3LiquidityPoolManager

        for pool_manager in pool_managers.values():
            if not isinstance(
                pool_manager, degenbot.UniswapV3LiquidityPoolManager
            ):
                continue
            try:
                v3_pool_helper = pool_manager.get_pool(
                    pool_address=event_address,
                    silent=True,
                    # WIP: use previous block state to avoid double-counting liquidity events
                    state_block=event_block - 1,
                )
            except degenbot.exceptions.ManagerError:
                continue
            else:
                v3_pool_manager = pool_manager
                break

        if v3_pool_helper is None:
            # ignore events for unknown pools
            return

        if removed:
            try:
                v3_pool_helper.restore_state_before_block(event_block)
            except degenbot.exceptions.NoPoolStateAvailable:
                # Remove the pool helper from AllPools
                del all_pools[v3_pool_helper]
                # Remove the pool helper from the pool manager
                del v3_pool_manager[v3_pool_helper]
                logger.info(
                    f"Removed pool helper {v3_pool_helper} at block {event_block}"
                )
            else:
                snapshot.update_snapshot(
                    pool=event_address,
                    tick_bitmap=v3_pool_helper.tick_bitmap,
                    tick_data=v3_pool_helper.tick_data,
                )
                logger.info(
                    f"Unwound state for pool {v3_pool_helper} at block {event_block}"
                )
            finally:
                return

        if TYPE_CHECKING:
            assert isinstance(v3_pool_helper, degenbot.V3LiquidityPool)

        try:
            _, _, lower, upper = message["result"]["topics"]
            event_tick_lower, *_ = eth_abi.abi.decode(
                types=("int24",), data=HexBytes(lower)
            )
            event_tick_upper, *_ = eth_abi.abi.decode(
                types=("int24",), data=HexBytes(upper)
            )
            event_liquidity, _, _ = eth_abi.abi.decode(
                types=("uint128", "uint256", "uint256"),
                data=HexBytes(event_data),
            )
        except KeyError:
            return

        if event_liquidity == 0:
            return

        event_liquidity *= -1

        try:
            # WIP: flipped snapshot update to after pool update. Is this right?
            v3_pool_helper.external_update(
                update=UniswapV3PoolExternalUpdate(
                    block_number=event_block,
                    liquidity_change=(
                        event_liquidity,
                        event_tick_lower,
                        event_tick_upper,
                    ),
                    tx=message["result"]["transactionHash"],
                ),
            )
            snapshot.update_snapshot(
                pool=event_address,
                tick_bitmap=v3_pool_helper.tick_bitmap,
                tick_data=v3_pool_helper.tick_data,
            )
        # WIP: sys.exit to kill the bot on a failed assert
        # looking to fix "assert self.liquidity >= 0" throwing on some Burn events
        except AssertionError:
            logger.exception(
                f"(process_burn_event) AssertionError: {message}"
            )
            sys.exit()
        except Exception:
            logger.exception("(process_burn_event)")

    def process_mint_event(message: dict, removed: bool = False):
        # Specification per https://github.com/Uniswap/v3-core/blob/main/contracts/interfaces/pool/IUniswapV3PoolEvents.sol#L21
        # event Mint(
        #     address sender,
        #     address indexed owner,
        #     int24 indexed tickLower,
        #     int24 indexed tickUpper,
        #     uint128 amount,
        #     uint256 amount0,
        #     uint256 amount1
        # );
        event_address = to_checksum_address(
            message["result"]["address"]
        )
        event_block = message["result"]["blockNumber"]
        if not isinstance(event_block, int):
            event_block = int.from_bytes(event_block)
        event_data = message["result"]["data"]

        v3_pool_helper: Optional[degenbot.V3LiquidityPool] = None
        v3_pool_manager: degenbot.UniswapV3LiquidityPoolManager

        for pool_manager in pool_managers.values():
            if not isinstance(
                pool_manager, degenbot.UniswapV3LiquidityPoolManager
            ):
                continue
            try:
                v3_pool_helper = pool_manager.get_pool(
                    pool_address=event_address,
                    silent=True,
                    # WIP: use previous block state to avoid double-counting liquidity events
                    state_block=event_block - 1,
                )
            except degenbot.exceptions.ManagerError:
                continue
            else:
                v3_pool_manager = pool_manager
                break

        if v3_pool_helper is None:
            # ignore events for unknown pools
            # print(f"(process_mint_event) Could not get pool {event_address}")
            return

        if removed:
            try:
                v3_pool_helper.restore_state_before_block(event_block)
            except degenbot.exceptions.NoPoolStateAvailable:
                # Remove the pool helper from AllPools
                del all_pools[v3_pool_helper]
                # Remove the pool helper from the pool manager
                del v3_pool_manager[v3_pool_helper]
                logger.info(
                    f"Removed pool helper {v3_pool_helper} at block {event_block}"
                )
            else:
                snapshot.update_snapshot(
                    pool=event_address,
                    tick_bitmap=v3_pool_helper.tick_bitmap,
                    tick_data=v3_pool_helper.tick_data,
                )
                logger.info(
                    f"Unwound state for pool {v3_pool_helper} at block {event_block}"
                )
            finally:
                return

        if TYPE_CHECKING:
            assert isinstance(v3_pool_helper, degenbot.V3LiquidityPool)

        try:
            _, _, lower, upper = message["result"]["topics"]
            event_tick_lower, *_ = eth_abi.abi.decode(
                types=("int24",), data=HexBytes(lower)
            )
            event_tick_upper, *_ = eth_abi.abi.decode(
                types=("int24",), data=HexBytes(upper)
            )
            _, event_liquidity, _, _ = eth_abi.abi.decode(
                types=("address", "uint128", "uint256", "uint256"),
                data=HexBytes(event_data),
            )
        except KeyError:
            return

        if event_liquidity == 0:
            return

        try:
            # WIP: flipped snapshot update to after pool update. Is this right?
            v3_pool_helper.external_update(
                update=UniswapV3PoolExternalUpdate(
                    block_number=event_block,
                    liquidity_change=(
                        event_liquidity,
                        event_tick_lower,
                        event_tick_upper,
                    ),
                    tx=message["result"]["transactionHash"],
                ),
            )
            snapshot.update_snapshot(
                pool=event_address,
                tick_bitmap=v3_pool_helper.tick_bitmap,
                tick_data=v3_pool_helper.tick_data,
            )
        except Exception:
            logger.exception("(process_mint_event)")

    def process_sync_event(message: dict, removed: bool = False):
        event_address = to_checksum_address(
            message["result"]["address"]
        )
        event_block = message["result"]["blockNumber"]
        if not isinstance(event_block, int):
            event_block = int.from_bytes(event_block)
        event_data = message["result"]["data"]

        event_reserves = eth_abi.abi.decode(
            types=("uint112", "uint112"),
            data=HexBytes(event_data),
        )

        v2_pool_helper: Optional[degenbot.LiquidityPool] = None
        v2_pool_manager: degenbot.UniswapV2LiquidityPoolManager

        for pool_manager in pool_managers.values():
            if not isinstance(
                pool_manager, degenbot.UniswapV2LiquidityPoolManager
            ):
                continue
            try:
                v2_pool_helper = pool_manager.get_pool(
                    pool_address=event_address,
                    state_block=event_block - 1,
                    silent=True,
                )
            except degenbot.exceptions.ManagerError:
                continue
            else:
                v2_pool_manager = pool_manager
                break

        if v2_pool_helper is None:
            # ignore events for unknown pools
            # print(f"(process_sync_event) Could not get pool {event_address}")
            return

        if removed:
            try:
                v2_pool_helper.restore_state_before_block(event_block)
            except degenbot.exceptions.NoPoolStateAvailable:
                # Remove the pool helper from AllPools
                del all_pools[v2_pool_helper]
                # Remove the pool helper from the pool manager
                del v2_pool_manager[v2_pool_helper]
                logger.info(
                    f"Removed pool helper {v2_pool_helper} at block {event_block}"
                )
            else:
                logger.info(
                    f"Unwound state for pool {v2_pool_helper} at block {event_block}"
                )
            finally:
                return

        reserves0, reserves1 = event_reserves

        if TYPE_CHECKING:
            assert isinstance(v2_pool_helper, degenbot.LiquidityPool)

        try:
            v2_pool_helper.update_reserves(
                external_token0_reserves=reserves0,
                external_token1_reserves=reserves1,
                silent=not VERBOSE_UPDATES,
                print_ratios=False,
                print_reserves=False,
                update_block=event_block,
            )
        except degenbot.exceptions.ExternalUpdateError:
            pass
        except Exception:
            logger.exception("(process_sync_event)")

    def process_swap_event(message: dict, removed: bool = False):
        # Specification per https://github.com/Uniswap/v3-core/blob/main/contracts/interfaces/pool/IUniswapV3PoolEvents.sol#L72:
        # event Swap(
        #     address indexed sender,
        #     address indexed recipient,
        #     int256 amount0,
        #     int256 amount1,
        #     uint160 sqrtPriceX96,
        #     uint128 liquidity,
        #     int24 tick
        # );

        event_address = to_checksum_address(
            message["result"]["address"]
        )
        event_block = message["result"]["blockNumber"]
        if not isinstance(event_block, int):
            event_block = int.from_bytes(event_block)
        event_data = message["result"]["data"]

        (
            _,
            _,
            event_sqrt_price_x96,
            event_liquidity,
            event_tick,
        ) = eth_abi.abi.decode(
            types=("int256", "int256", "uint160", "uint128", "int24"),
            data=HexBytes(event_data),
        )

        v3_pool_helper: degenbot.V3LiquidityPool | None = None
        v3_pool_manager: degenbot.UniswapV3LiquidityPoolManager

        for pool_manager in pool_managers.values():
            if not isinstance(
                pool_manager, degenbot.UniswapV3LiquidityPoolManager
            ):
                continue
            try:
                v3_pool_helper = pool_manager.get_pool(
                    pool_address=event_address,
                    silent=True,
                    state_block=event_block - 1,
                )
            except degenbot.exceptions.ManagerError:
                continue
            else:
                v3_pool_manager = pool_manager
                break

        if v3_pool_helper is None:
            # ignore events for unknown pools
            # print(f"(process_swap_event) Could not get pool {event_address}")
            return

        if removed:
            try:
                v3_pool_helper.restore_state_before_block(event_block)
            except degenbot.exceptions.NoPoolStateAvailable:
                # Remove the pool helper from AllPools
                del all_pools[v3_pool_helper]
                # Remove the pool helper from the pool manager
                del v3_pool_manager[v3_pool_helper]
                logger.info(
                    f"Removed pool helper {v3_pool_helper} at block {event_block}"
                )
            else:
                snapshot.update_snapshot(
                    pool=event_address,
                    tick_bitmap=v3_pool_helper.tick_bitmap,
                    tick_data=v3_pool_helper.tick_data,
                )
                logger.info(
                    f"Unwound state for pool {v3_pool_helper} at block {event_block}"
                )
            finally:
                return

        if TYPE_CHECKING:
            assert isinstance(v3_pool_helper, degenbot.V3LiquidityPool)

        try:
            v3_pool_helper.external_update(
                update=UniswapV3PoolExternalUpdate(
                    block_number=event_block,
                    liquidity=event_liquidity,
                    tick=event_tick,
                    sqrt_price_x96=event_sqrt_price_x96,
                    tx=message["result"]["transactionHash"],
                ),
            )
        except Exception:
            logger.exception("(process_swap_event)")

    def process_new_v2_pool_event(message: dict, removed: bool = False):
        event_address = to_checksum_address(
            message["result"]["address"]
        )
        event_data = message["result"]["data"]
        event_block = message["result"]["blockNumber"]
        if not isinstance(event_block, int):
            event_block = int.from_bytes(event_block)
        # token0_address = message["result"]["topics"][1]
        # token1_address = message["result"]["topics"][2]

        pool_address, _ = eth_abi.abi.decode(
            types=("address", "uint256"),
            data=HexBytes(event_data),
        )

        try:
            pool_manager = degenbot.UniswapV2LiquidityPoolManager(
                factory_address=event_address
            )
        except Exception:
            return

        if removed:
            try:
                v2_pool_helper = pool_manager.get_pool(
                    pool_address=pool_address,
                    silent=True,
                )
            except degenbot.exceptions.ManagerError:
                pass
            else:
                # Revert the pool to the initial state (empty)
                v2_pool_helper.restore_state_before_block(1)
                logger.info(
                    f"Reset pool helper {v2_pool_helper} to initial state: {v2_pool_helper.state=}"
                )
                # # Remove the pool helper from AllPools
                # del all_pools[v2_pool_helper]
                # # Remove the pool helper from the pool manager
                # del pool_manager[v2_pool_helper]
            finally:
                return

        try:
            pool_helper = pool_manager.get_pool(
                pool_address=pool_address,
                state_block=event_block,
                silent=True,
            )
        except Exception as e:
            logger.error(f"{type(e)}: {e}")
            logger.error(f"{message=}")
            return
        else:
            logger.info(
                f"Created new V2 pool at block {event_block}: {pool_helper}"
            )

    def process_new_v3_pool_event(message: dict, removed: bool = False):
        event_data = message["result"]["data"]
        event_block = message["result"]["blockNumber"]
        if not isinstance(event_block, int):
            event_block = int.from_bytes(event_block)
        event_address = message["result"]["address"]
        # token0_address = message["result"]["topics"][1]
        # token1_address = message["result"]["topics"][2]
        # fee = message["result"]["topics"][3]

        _, pool_address = eth_abi.abi.decode(
            types=("int24", "address"),
            data=HexBytes(event_data),
        )

        try:
            pool_manager = degenbot.UniswapV3LiquidityPoolManager(
                factory_address=event_address
            )
        except Exception as exc:
            print(exc)
            return

        if removed:
            try:
                v3_pool_helper = pool_manager.get_pool(
                    pool_address=pool_address, silent=True
                )
            except degenbot.exceptions.ManagerError:
                pass
            else:
                # Revert the pool to the initial state (empty)
                v3_pool_helper.restore_state_before_block(1)
                logger.info(
                    f"Reset pool helper {v3_pool_helper} to initial state: {v3_pool_helper.state=}"
                )
                # # Remove the pool helper from AllPools
                # del all_pools[v3_pool_helper]
                # # Remove the pool helper from the pool manager
                # del pool_manager[v3_pool_helper]
            finally:
                return

        try:
            pool_helper = pool_manager.get_pool(
                pool_address=pool_address,
                state_block=event_block,
                silent=True,
            )
        except Exception as exc:
            print(exc)
            return
        else:
            logger.info(
                f"Created new V3 pool at block {event_block}: {pool_helper}"
            )
            assert pool_helper._sparse_bitmap is False

    def process_curve_token_exchange_event(
        message: dict, removed: bool = False
    ):
        curve_pool_helper = all_pools.get(message["result"]["address"])
        if curve_pool_helper is None:
            return

        if TYPE_CHECKING:
            assert isinstance(
                curve_pool_helper, degenbot.CurveStableswapPool
            )

        curve_pool_helper.auto_update()
        logger.info(f"Updated Curve pool: {curve_pool_helper}")

    class ProcessingParams(TypedDict):
        name: str
        process_func: Callable[[dict, bool], None]

    EVENTS: Dict[HexBytes, ProcessingParams] = {
        web3.Web3.keccak(
            text="Sync(uint112,uint112)",
        ): {
            "name": "Uniswap V2: SYNC",
            "process_func": process_sync_event,
        },
        web3.Web3.keccak(
            text="Mint(address,address,int24,int24,uint128,uint256,uint256)"
        ): {
            "name": "Uniswap V3: MINT",
            "process_func": process_mint_event,
        },
        web3.Web3.keccak(
            text="Burn(address,int24,int24,uint128,uint256,uint256)"
        ): {
            "name": "Uniswap V3: BURN",
            "process_func": process_burn_event,
        },
        web3.Web3.keccak(
            text="Swap(address,address,int256,int256,uint160,uint128,int24)"
        ): {
            "name": "Uniswap V3: SWAP",
            "process_func": process_swap_event,
        },
        web3.Web3.keccak(
            text="PairCreated(address,address,address,uint256)"
        ): {
            "name": "Uniswap V2: POOL CREATED",
            "process_func": process_new_v2_pool_event,
        },
        web3.Web3.keccak(
            text="PoolCreated(address,address,uint24,int24,address)"
        ): {
            "name": "Uniswap V3: POOL CREATED",
            "process_func": process_new_v3_pool_event,
        },
        web3.Web3.keccak(
            text="TokenExchange(address,int128,uint256,int128,uint256)"
        ): {
            "name": "Curve V1: TOKEN EXCHANGE",
            "process_func": process_curve_token_exchange_event,
        },
        web3.Web3.keccak(
            text="TokenExchangeUnderlying(address,int128,uint256,int128,uint256)"
        ): {
            "name": "Curve V1: TOKEN EXCHANGE UNDERLYING",
            "process_func": process_curve_token_exchange_event,
        },
        web3.Web3.keccak(
            text="AddLiquidity(address,uint256[4],uint256[4],uint256,uint256)"
        ): {
            "name": "Curve V1: ADD LIQUIDITY (4 coins)",
            "process_func": process_curve_token_exchange_event,
        },
        web3.Web3.keccak(
            text="AddLiquidity(address,uint256[3],uint256[3],uint256,uint256)"
        ): {
            "name": "Curve V1: ADD LIQUIDITY (3 coins)",
            "process_func": process_curve_token_exchange_event,
        },
        web3.Web3.keccak(
            text="AddLiquidity(address,uint256[2],uint256[2],uint256,uint256)"
        ): {
            "name": "Curve V1: ADD LIQUIDITY (2 coins)",
            "process_func": process_curve_token_exchange_event,
        },
        web3.Web3.keccak(
            text="RemoveLiquidity(address,uint256[4],uint256[4],uint256)"
        ): {
            "name": "Curve V1: REMOVE LIQUIDITY (4 coins)",
            "process_func": process_curve_token_exchange_event,
        },
        web3.Web3.keccak(
            text="RemoveLiquidity(address,uint256[3],uint256[3],uint256)"
        ): {
            "name": "Curve V1: REMOVE LIQUIDITY (3 coins)",
            "process_func": process_curve_token_exchange_event,
        },
        web3.Web3.keccak(
            text="RemoveLiquidity(address,uint256[2],uint256[2],uint256)"
        ): {
            "name": "Curve V1: REMOVE LIQUIDITY (2 coins)",
            "process_func": process_curve_token_exchange_event,
        },
        web3.Web3.keccak(
            text="RemoveLiquidityOne(address,uint256,uint256)"
        ): {
            "name": "Curve V1: REMOVE LIQUIDITY (1 coin)",
            "process_func": process_curve_token_exchange_event,
        },
        web3.Web3.keccak(
            text="RemoveLiquidityImbalance(address,uint256[4],uint256[4],uint256,uint256)"
        ): {
            "name": "Curve V1: REMOVE LIQUIDITY IMBALANCE (4 coins)",
            "process_func": process_curve_token_exchange_event,
        },
        web3.Web3.keccak(
            text="RemoveLiquidityImbalance(address,uint256[3],uint256[3],uint256,uint256)"
        ): {
            "name": "Curve V1: REMOVE LIQUIDITY IMBALANCE (3 coins)",
            "process_func": process_curve_token_exchange_event,
        },
        web3.Web3.keccak(
            text="RemoveLiquidityImbalance(address,uint256[2],uint256[2],uint256,uint256)"
        ): {
            "name": "Curve V1: REMOVE LIQUIDITY IMBALANCE (2 coins)",
            "process_func": process_curve_token_exchange_event,
        },
    }

    logger.info("Starting subscription loop")
    logger.info("Listening for events:")
    for _, _event_info in EVENTS.items():
        logger.info(f'{_event_info["name"]}')

    try:
        while not bot_status.live:
            await asyncio.sleep(1)

        last_event_count = 0

        # This loop runs forever, consuming the event queue
        while True:
            # Allow the queue to fill until it stops growing
            if not events or last_event_count < len(events):
                last_event_count = len(events)
                await asyncio.sleep(EVENT_PROCESS_DELAY)
                continue

            # process the queue completely
            while events:
                event = events.popleft()

                try:
                    topic0: HexBytes = event["result"]["topics"][0]
                    process_func: Callable = EVENTS[topic0][
                        "process_func"
                    ]
                    process_func(
                        event,
                        event["result"]["removed"],
                    )
                except (KeyError, IndexError):
                    # Ignore topics without a handler
                    continue
                else:
                    if VERBOSE_PROCESSING:
                        logger.info(
                            f"processed {EVENTS[topic0]['name']} event - {len(events)} remaining"
                        )

            await asyncio.sleep(0)  # yield control to the event loop

    except asyncio.exceptions.CancelledError:
        return


async def subscription_watcher(
    bot_status: BotStatus,
    events: deque,
    pending_tx,
    backrun_hashes,
    w3: web3.Web3,
    http_session: aiohttp.ClientSession,
    process_pool: ProcessPoolExecutor,
    tasks: Set[asyncio.Task],
    all_arbs,
):
    # A 5 minute rolling window of block numbers and timestamps, seeded with initial values
    block_times = deque(
        [
            (
                bot_status.current_block - 1,
                bot_status.current_block_timestamp
                - int(AVERAGE_BLOCK_TIME),
            ),
            (
                bot_status.current_block,
                bot_status.current_block_timestamp,
            ),
        ],
        maxlen=int(5 * 60 / AVERAGE_BLOCK_TIME),
    )

    last_block: Optional[int] = None

    # reset the first block and status every time every time the watcher connects
    bot_status.watching_blocks = False
    bot_status.first_block = 0

    async def handle_event(message: dict):
        if not bot_status.first_event:
            bot_status.first_event = message["result"]["blockNumber"]
            logger.info(f"First event block: {bot_status.first_event}")
        events.append(message)

    async def handle_block(message: dict):
        block_number = message["result"]["number"]

        bot_status.current_block = (
            block_number
            if isinstance(block_number, int)
            else int(block_number, 16)
        )

        block_timestamp = message["result"]["timestamp"]
        if not isinstance(block_timestamp, int):
            block_timestamp = int(block_timestamp, 16)
        bot_status.current_block_timestamp = block_timestamp

        block_base_fee = message["result"]["baseFeePerGas"]
        if not isinstance(block_base_fee, int):
            block_base_fee = int(block_base_fee, 16)
        bot_status.base_fee = block_base_fee

        block_gas_used = message["result"]["gasUsed"]
        if not isinstance(block_gas_used, int):
            block_gas_used = int(block_gas_used, 16)

        block_gas_limit = message["result"]["gasLimit"]
        if not isinstance(block_gas_limit, int):
            block_gas_limit = int(block_gas_limit, 16)

        nonlocal last_block
        if last_block is None:
            last_block = bot_status.current_block

        block_times.append(
            (
                bot_status.current_block,
                bot_status.current_block_timestamp,
            )
        )

        (
            oldest_block_number,
            oldest_block_timestamp,
        ) = block_times[0]

        bot_status.average_blocktime = (
            bot_status.current_block_timestamp - oldest_block_timestamp
        ) / (bot_status.current_block - oldest_block_number)

        if not bot_status.first_block:
            bot_status.first_block = bot_status.current_block
            logger.info(f"First full block: {bot_status.first_block}")

        bot_status.base_fee_next = degenbot.next_base_fee(
            parent_base_fee=block_base_fee,
            parent_gas_used=block_gas_used,
            parent_gas_limit=block_gas_limit,
        )

        last_block = bot_status.current_block

        if VERBOSE_BLOCKS:
            logger.info(
                f"[{bot_status.current_block}]"
                f"[+{time.time() - bot_status.current_block_timestamp:.1f}s]"
                f"[{bot_status.base_fee/(10**9):.1f}/{bot_status.base_fee_next/(10**9):.1f}]"
                f", {len(pending_tx)} seen"
                f", {len(backrun_hashes)} sent"
                f", {bot_status.number_of_tx_processing} processing"
            )

    async def handle_pending_transaction(message: dict):
        if SUBSCRIBE_TO_FULL_TRANSACTIONS:
            transaction = dict(message["result"])
            transaction_hash = message["result"]["hash"]
        else:
            transaction = None
            transaction_hash = message["result"]

        # await process_pending_transaction(
        #     w3=w3,
        #     bot_status=bot_status,
        #     pending_tx=pending_tx,
        #     http_session=http_session,
        #     all_arbs=all_arbs,
        #     tasks=tasks,
        #     backrun_hashes=backrun_hashes,
        #     process_pool=process_pool,
        #     transaction=transaction,
        #     transaction_hash=transaction_hash,
        # )

        task = asyncio.create_task(
            process_pending_transaction(
                w3=w3,
                bot_status=bot_status,
                pending_tx=pending_tx,
                http_session=http_session,
                all_arbs=all_arbs,
                tasks=tasks,
                backrun_hashes=backrun_hashes,
                process_pool=process_pool,
                transaction=transaction,
                transaction_hash=transaction_hash,
            )
        )
        bot_status.number_of_tx_processing += 1
        task.add_done_callback(tasks.discard)
        task.add_done_callback(
            functools.partial(process_done, bot_status)
        )
        tasks.add(task)

    _SUBSCRIPTIONS: Dict[str, Callable] = {}

    async for watcher in web3.AsyncWeb3.persistent_websocket(
        web3.WebsocketProviderV2(endpoint_uri=NODE_WEBSOCKET_URI)
    ):
        events_subscription_id = await watcher.eth.subscribe(
            subscription_type="logs", subscription_arg={}
        )
        logger.info(
            f"Subscription Active: Events - {events_subscription_id}"
        )
        _SUBSCRIPTIONS[events_subscription_id] = handle_event

        new_blocks_subscription_id = await watcher.eth.subscribe(
            subscription_type="newHeads"
        )
        logger.info(
            f"Subscription Active: New Blocks - {new_blocks_subscription_id}"
        )
        _SUBSCRIPTIONS[new_blocks_subscription_id] = handle_block

        pending_tx_subscription_id = await watcher.eth.subscribe(
            subscription_type="newPendingTransactions",
            subscription_arg=SUBSCRIBE_TO_FULL_TRANSACTIONS,
        )
        logger.info(
            f"Subscription Active: Pending Transactions - {pending_tx_subscription_id}"
        )
        _SUBSCRIPTIONS[
            pending_tx_subscription_id
        ] = handle_pending_transaction

        try:
            async for message in watcher.ws.process_subscriptions():
                subscription_id = message["subscription"]
                handler = _SUBSCRIPTIONS[subscription_id]
                await handler(message)
        except websockets.exceptions.ConnectionClosed:
            continue
        except asyncio.CancelledError:
            return


def process_done(bot_status: BotStatus, *args):
    bot_status.processing_tx = False
    bot_status.number_of_tx_processing -= 1


async def process_pending_transaction(
    w3: web3.Web3,
    bot_status: BotStatus,
    pending_tx: Dict[HexBytes, dict | None],
    http_session: aiohttp.ClientSession,
    all_arbs: Dict[str, UniswapCurveCycle],
    tasks: Set[asyncio.Task],
    backrun_hashes: Set,
    process_pool: ProcessPoolExecutor,
    transaction_hash: HexBytes,
    transaction: Optional[dict] = None,
    raw_transaction: Optional[HexBytes] = None,
) -> None:
    if any(
        [
            bot_status.paused is True,
            bot_status.live is False,
            bot_status.processing_tx is True,
        ]
    ):
        return

    # Skip if TX already seen
    if transaction_hash in pending_tx:
        return

    bot_status.processing_tx = True
    _start = time.perf_counter()
    state_block = bot_status.current_block

    if transaction is None:
        try:
            transaction = dict(w3.eth.get_transaction(transaction_hash))
        except web3.exceptions.TransactionNotFound:
            return
        except Exception as exc:
            print(f"{type(exc)}: {exc}")
            return

    # Drop simple Ether transfers (no calldata)
    if not transaction["input"]:
        return

    # Drop contract creations
    if (tx_destination := transaction.get("to")) is None:
        return

    if tx_destination not in ROUTERS:
        return

    if raw_transaction is None:
        try:
            raw_transaction = w3.eth.get_raw_transaction(
                transaction_hash
            )
            # raw_transaction = HexBytes("0x02") + rlp.encode(
            #     [
            #         transaction["chainId"],
            #         transaction["nonce"],
            #         transaction["maxPriorityFeePerGas"],
            #         transaction["maxFeePerGas"],
            #         transaction["gas"],
            #         HexBytes(transaction["to"]),
            #         transaction["value"],
            #         transaction["input"],
            #         transaction["accessList"],
            #         transaction["v"],
            #         transaction["r"],
            #         transaction["s"],
            #     ]
            # )
        except web3.exceptions.TransactionNotFound:
            # print("could not retrieve raw transaction")
            return
        except Exception as exc:
            print(f"{type(exc)}: {exc}")
            return

    pending_tx[transaction_hash] = transaction

    try:
        params_to_keep = set(
            [
                "from",
                "to",
                "gas",
                "maxFeePerGas",
                "maxPriorityFeePerGas",
                "gasPrice",
                "value",
                "data",
                "input",
                "nonce",
                "type",
            ]
        )

        transaction["type"] = int(transaction["type"])
        # if isinstance(transaction["input"], HexBytes):
        #     transaction["input"] = transaction["input"].hex()
        if transaction["type"] == 0:
            params_to_keep.remove("maxFeePerGas")
            params_to_keep.remove("maxPriorityFeePerGas")
        elif transaction["type"] == 1:
            params_to_keep.remove("maxFeePerGas")
            params_to_keep.remove("maxPriorityFeePerGas")
        elif transaction["type"] == 2:
            params_to_keep.remove("gasPrice")
        else:
            logger.error(f'Unknown TX type: {transaction["type"]}')
            logger.error(f"{transaction=}")
            return

        tx_dict = TxParams(
            **{
                k: v
                for k, v in transaction.items()
                if k in params_to_keep
            }
        )
        w3.eth.call(
            transaction=tx_dict,
            block_identifier=state_block,
        )
    except web3.exceptions.ContractLogicError:
        # print(f"{type(e)}, {transaction_hash.hex()}, {e}")
        return
    except ValueError as e:
        error_message = str(e).lower()
        # print(f"{error_message=}")
        if "nonce too low" in error_message:
            # Can never be valid. Keep the hash, discard the TX
            pass
        elif (
            "max fee per gas less than block base fee" in error_message
        ):
            # discard the TX, assume it will linger too long to be profitable
            pass
        elif "out of gas" in error_message:
            pass
        else:
            print(f"{type(e)}, {transaction_hash.hex()}, {e}")
        pending_tx[transaction_hash] = None
        return
    except Exception as e:
        print(f"{type(e)}, {transaction_hash.hex()}, {e}")
        return

    try:
        tx_input = transaction["input"]
        tx_nonce = transaction["nonce"]
        tx_value = transaction["value"]
        tx_sender = transaction["from"]
    except KeyError:
        return

    try:
        func_object, func_parameters = w3.eth.contract(
            address=tx_destination,
            abi=ROUTERS[tx_destination]["abi"],
        ).decode_function_input(tx_input)
    except ValueError as e:
        # Thrown when the function cannot be decoded
        print(f"(decode) {type(e)}, {transaction_hash.hex()}, {e}")
        return
    except Exception:
        logger.exception(
            "(watch_pending_transactions) decode_function_input"
        )
        return

    try:
        tx_helper = degenbot.UniswapTransaction(
            tx_hash=transaction_hash,
            chain_id=bot_status.chain_id,
            func_name=func_object.fn_name,
            func_params=func_parameters,
            tx_nonce=tx_nonce,
            tx_value=tx_value,
            tx_sender=tx_sender,
            router_address=tx_destination,
        )
    except degenbot.exceptions.TransactionError as e:
        logger.info(f"UniswapTransaction - {type(e)}:{e}")
        return

    try:
        sim_results = tx_helper.simulate(silent=True)
    except degenbot.exceptions.ManagerError as e:
        logger.info(f"(watch_events.simulate) (ManagerError): {e}")
        return
    except degenbot.exceptions.TransactionError as e:
        logger.debug(f"(watch_events.simulate) (TransactionError): {e}")
        return
    except Exception as e:
        logger.info(f"{type(e)}: {e}")
        logger.info(f"{transaction=}")
        sys.exit()

    # Cache the set of pools in the TX
    pool_set = set([pool for pool, _ in sim_results])

    # Find arbitrage helpers using pools along the TX path
    arb_helpers = [
        arb_helper
        for pool in pool_set
        for arb_helper in list(pool.get_arbitrage_helpers())
    ]

    if not arb_helpers:
        return

    calculation_futures = []
    for arb_helper in arb_helpers:
        if TYPE_CHECKING:
            assert isinstance(arb_helper, UniswapCurveCycle)
        try:
            calculation_futures.append(
                await arb_helper.calculate_with_pool(
                    executor=process_pool,
                    override_state=sim_results,
                )
            )
        except degenbot.exceptions.ArbitrageError:
            pass
        except Exception:
            logger.error(f"Arb: {arb_helper}")
            logger.error(f"ID : {arb_helper.id}")
            logger.exception(
                "(process_pending_transactions) building calculation_futures"
            )

    if not calculation_futures:
        return

    # logger.info(
    #     f"Reduced {len(arb_helpers)} helpers to {len(calculation_futures)}. {time.perf_counter() - _start:.2f}s since start"
    # )

    calculation_results: List[ArbitrageCalculationResult] = []

    for task in asyncio.as_completed(
        calculation_futures,
        # timeout=2.0,
    ):
        try:
            calculation_results.append(await task)
        except degenbot.exceptions.ArbitrageError:
            # logger.info(f"calculate_with_pool: {exc}")
            continue
        except asyncio.exceptions.TimeoutError:
            logger.info(
                f"Stopped early, calculated {len(calculation_results)} of {len(calculation_futures)}."
            )
            break
        except RuntimeError:
            logger.exception("RuntimeError")
            sys.exit()
            continue
        except Exception:
            logger.exception(
                "process_pending_transactions.as_completed(calculation_futures)"
            )
            continue

    calculation_futures.clear()

    # logger.info(
    #     f"Got results for {len(calculation_results)} arbs. {time.perf_counter() - _start:.2f}s since start"
    # )

    # sort the arb helpers by profit
    all_profitable_calc_results = sorted(
        [
            calc_result
            for calc_result in calculation_results
            if calc_result.profit_amount >= MIN_PROFIT_GROSS
        ],
        key=lambda calc_result: calc_result.profit_amount,
        reverse=True,
    )

    all_profitable_arbs = [
        all_arbs[calc_result.id]
        for calc_result in all_profitable_calc_results
    ]

    # pair them up for matching later
    results_by_arb_id: Dict[str, ArbitrageCalculationResult] = dict()
    for calc_result, arb in zip(
        all_profitable_calc_results,
        all_profitable_arbs,
        strict=True,
    ):
        if TYPE_CHECKING:
            assert arb is not None
        results_by_arb_id[arb.id] = calc_result

    if not all_profitable_arbs:
        return

    arbs_without_overlap: Set[UniswapCurveCycle] = set()

    while True:
        most_profitable_arb = all_profitable_arbs.pop(0)
        if TYPE_CHECKING:
            assert most_profitable_arb is not None
        arbs_without_overlap.add(most_profitable_arb)

        conflicting_arbs = [
            arb_helper
            for arb_helper in all_profitable_arbs
            if set(most_profitable_arb.swap_pools)
            & set(arb_helper.swap_pools)
        ]

        # Drop conflicting arbs from working set
        for arb in conflicting_arbs:
            all_profitable_arbs.remove(arb)

        if not all_profitable_arbs:
            break

    for arb_helper in arbs_without_overlap:
        arb_result = results_by_arb_id[arb_helper.id]

        if TYPE_CHECKING:
            assert isinstance(raw_transaction, HexBytes)

        logger.info(
            f"Sending arb {arb_helper}, {arb_helper.id=}, backrunning {transaction_hash.hex()}. {time.perf_counter() - _start:.2f}s since start"
        )

        await send_to_builders(
            w3=w3,
            http_session=http_session,
            arb_result=arb_result,
            bot_status=bot_status,
            all_arbs=all_arbs,
            state_block=state_block,
            target_block=state_block + 1,
            tx_to_backrun=BackrunTx(
                tx=transaction,
                raw=raw_transaction,
                hash=transaction_hash,
            ),
            backrun_set=backrun_hashes,
        )

        # task = asyncio.create_task(
        #     send_to_builders(
        #         w3=w3,
        #         http_session=http_session,
        #         arb_result=arb_result,
        #         bot_status=bot_status,
        #         all_arbs=all_arbs,
        #         state_block=bot_status.current_block,
        #         target_block=bot_status.current_block + 1,
        #         tx_to_backrun={
        #             "tx": transaction,
        #             "raw": raw_transaction.hex(),
        #             "hash": transaction_hash,
        #         },
        #         backrun_set=backrun_hashes,
        #     )
        # )
        # task.add_done_callback(tasks.discard)
        # tasks.add(task)


if __name__ == "__main__":
    logger = logging.getLogger("ethereum_backrun_mempool_curve_cycle")
    logger.propagate = False
    logger.setLevel(logging.INFO)
    logger_formatter = logging.Formatter("%(levelname)s - %(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logger_formatter)
    logger.addHandler(stream_handler)

    if not DRY_RUN:
        logger.info("")
        logger.info("***************************************")
        logger.info("*** DRY RUN DISABLED - BOT IS LIVE! ***")
        logger.info("***************************************")
        logger.info("")

    # load historical submitted bundles
    SUBMITTED_BUNDLES = {}
    try:
        with open("submitted_bundles.json") as file:
            SUBMITTED_BUNDLES = ujson.load(file)
    # if the file doesn't exist, create it
    except FileNotFoundError:
        with open("submitted_bundles.json", "w") as file:
            ujson.dump(SUBMITTED_BUNDLES, file, indent=2)
    logger.info(f"Found {len(SUBMITTED_BUNDLES)} submitted bundles")

    BLACKLISTED_POOLS = []
    for blacklisted_pools_filename in [
        "ethereum_blacklisted_pools.json"
    ]:
        try:
            with open(
                blacklisted_pools_filename, encoding="utf-8"
            ) as file:
                BLACKLISTED_POOLS.extend(ujson.load(file))
        except FileNotFoundError:
            with open(
                blacklisted_pools_filename, "w", encoding="utf-8"
            ) as file:
                ujson.dump(BLACKLISTED_POOLS, file, indent=2)
    logger.info(f"Found {len(BLACKLISTED_POOLS)} blacklisted pools")

    BLACKLISTED_TOKENS = []
    for blacklisted_tokens_filename in [
        "ethereum_blacklisted_tokens.json"
    ]:
        try:
            with open(
                blacklisted_tokens_filename, encoding="utf-8"
            ) as file:
                BLACKLISTED_TOKENS.extend(ujson.load(file))
        except FileNotFoundError:
            with open(
                blacklisted_tokens_filename, "w", encoding="utf-8"
            ) as file:
                ujson.dump(BLACKLISTED_TOKENS, file, indent=2)
    logger.info(f"Found {len(BLACKLISTED_TOKENS)} blacklisted tokens")

    BLACKLISTED_ARBS = []
    for blacklisted_arbs_filename in ["ethereum_blacklisted_arbs.json"]:
        try:
            with open(
                blacklisted_arbs_filename, encoding="utf-8"
            ) as file:
                BLACKLISTED_ARBS.extend(ujson.load(file))
        except FileNotFoundError:
            with open(
                blacklisted_arbs_filename, "w", encoding="utf-8"
            ) as file:
                ujson.dump(BLACKLISTED_ARBS, file, indent=2)
    logger.info(f"Found {len(BLACKLISTED_ARBS)} blacklisted arbs")

    start = time.perf_counter()
    asyncio.run(main())
    logger.info(f"Completed in {time.perf_counter() - start:.2f}s")