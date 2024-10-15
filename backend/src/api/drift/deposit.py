
from src.api.drift.api import DriftAPI
from decimal import Decimal
import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Tuple, Union
from dotenv import load_dotenv
from spl.token.async_client import AsyncToken
from spl.token.constants import TOKEN_PROGRAM_ID

from anchorpy import Wallet # type: ignore
from solders.keypair import Keypair # type: ignore
from solders.pubkey import Pubkey # type: ignore
from solana.rpc.async_api import AsyncClient
from driftpy.math.amm import calculate_bid_ask_price
from driftpy.math.conversion import convert_to_number
from driftpy.math.market import (calculate_bid_price, calculate_ask_price)
from driftpy.types import (
    MarketType,
    OrderType,
    OrderParams,
    PositionDirection,
    PerpPosition,
    SpotPosition,
    UserAccount,
    Order,
    ModifyOrderParams, 
    OraclePriceData,
    PostOnlyParams,
    Order,
    TxParams
)
from driftpy.drift_client import DriftClient
from driftpy.math.perp_position import calculate_entry_price
from driftpy.account_subscription_config import AccountSubscriptionConfig, BulkAccountLoader
from driftpy.constants.config import configs
from driftpy.constants.perp_markets import (devnet_perp_market_configs, mainnet_perp_market_configs)
from driftpy.constants.spot_markets import (devnet_spot_market_configs, mainnet_spot_market_configs)
from driftpy.constants.numeric_constants import BASE_PRECISION, PRICE_PRECISION
from driftpy.math.spot_position import (
    get_worst_case_token_amounts,
    is_spot_position_available,
)

from driftpy.math.perp_position import (
    calculate_position_pnl,
    calculate_entry_price,
    calculate_base_asset_value,
    is_available
)
from driftpy.keypair import load_keypair
from src.common.types import MarketAccountType, PositionType
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)
from solana.rpc import commitment
import pprint


async def run_drift_api_initialize():
    # Load environment variables from .env file
    load_dotenv()

    # Create DriftAPI instance
    drift_api = DriftAPI("devnet")

    try:
        # Run initialize method
        await drift_api.initialize(subscription_type="polling")
        
        print("Initialization successful!")
        print(f"Public key: {drift_api.drift_client.wallet.payer.pubkey()}")
        
        # Additional checks
        print(f"Connection established: {drift_api.connection is not None}")
        print(f"Drift client initialized: {drift_api.drift_client is not None}")

    except Exception as e:
        print(f"Initialization failed: {str(e)}")
    
    # finally:
    #     # Clean up resources
    #     if hasattr(drift_api, 'connection') and drift_api.connection:
    #         await drift_api.connection.close()

# if __name__ == "__main__":
#     asyncio.run(run_drift_api_initialize())

async def test_place_order():
    load_dotenv()
    drift_api = DriftAPI("devnet")

    try:
        await drift_api.initialize(subscription_type="cached")
        # await drift_api.drift_client.subscribe()
        # await drift_api.drift_client.add_user(0)

        # order_params = OrderParams(
        #     market_index=0,  # Assuming BTC-PERP is at index 0
        #     market_type=MarketType.Perp(),
        #     order_type=OrderType.Limit(),
        #     direction=PositionDirection.Long(),
        #     base_asset_amount=int(0.001 * BASE_PRECISION),  # Convert to native units
        #     price=int(30000 * PRICE_PRECISION),  # Convert to native units
        #     reduce_only=False,
        #     post_only=True,
        # )

        order_params = OrderParams(
            market_type=MarketType.Perp(),
            order_type=OrderType.Limit(),
            base_asset_amount=drift_api.drift_client.convert_to_perp_precision(1),
            market_index=0,
            direction=PositionDirection.Long(),
            price=drift_api.drift_client.convert_to_price_precision(21.88),
            post_only=PostOnlyParams.TryPostOnly(),
        )

        await drift_api.place_order(order_params)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    # finally:
    #     if hasattr(drift_api, 'connection') and drift_api.connection:
    #         await drift_api.connection.close()

# if __name__ == "__main__":
#     asyncio.run(test_place_order())
#     #asyncio.run(run_drift_api_initialize())

async def test_get_open_orders():
    load_dotenv()
    drift_api = DriftAPI("devnet")

    try:
        await drift_api.initialize(subscription_type="polling")
        
        order_params = OrderParams(
            market_type=MarketType.Perp(),
            order_type=OrderType.Limit(),
            base_asset_amount=drift_api.drift_client.convert_to_perp_precision(0.01),
            market_index=0,
            direction=PositionDirection.Long(),
            price=drift_api.drift_client.convert_to_price_precision(30000),
            post_only=PostOnlyParams.TryPostOnly(),
        )

        #await drift_api.place_order(order_params)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    #await asyncio.sleep(5)  # Wait for 5 seconds
    try:
        #await drift_api.initialize(subscription_type="cached")
        
        #await drift_api.drift_client.get_user().subscribe()
        open_orders = drift_api.get_open_orders()
        await asyncio.sleep(20)  # Wait for 5 seconds
        # print(f"open_orders: {open_orders}")

        
        # print(f"Number of open orders: {len(open_orders)}")
        # for order in open_orders:
        #     print(f"Order ID: {order.order_id}")
        #     print(f"Market Index: {order.market_index}")
        #     print(f"Market Type: {order.market_type}")
        #     print(f"Direction: {order.direction}")
        #     print(f"Base Asset Amount: {order.base_asset_amount}")
        #     print(f"Price: {order.price}")
        #     print("---")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    # finally:
    #     if hasattr(drift_api, 'connection') and drift_api.connection:
    #         await drift_api.connection.close()

# if __name__ == "__main__":
#     asyncio.run(test_get_open_orders())

async def test_drift_api():
    load_dotenv()
    keypath = os.getenv("DRIFT_WALLET_PRIVATE_KEY")
    url = os.getenv("RPC_URL")

    if not keypath:
        raise ValueError("DRIFT_WALLET_PRIVATE_KEY not set in environment variables")
    if not url:
        raise ValueError("RPC_URL not set in environment variables")
    try:
        with open(os.path.expanduser(keypath), "r") as f:
            secret = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Private key file not found at {keypath}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in private key file at {keypath}")

    #keypair = load_keypair(secret)
    keypair = Keypair.from_bytes(bytes(secret))
    wallet = Wallet(keypair)

    #logger.info(f"Using public key: {keypair.pubkey()}")
    connection = AsyncClient(url)
    bulk_account_loader = BulkAccountLoader(connection)

    drift_client = DriftClient(
        connection,
        wallet,
        "devnet", # using devnet 
        tx_params=TxParams(600_000, 100),
        account_subscription=AccountSubscriptionConfig("polling", bulk_account_loader=bulk_account_loader)
    )

    # drift_client = DriftClient(
    #     connection,
    #     wallet,
    #     "mainnet",
    #     account_subscription=AccountSubscriptionConfig("websocket"),
    #     tx_params=TxParams(300_000, 100_000),
    #     active_sub_account_id=sub_account_id,
    # )

    #await drift_client.add_user(sub_account_id)
    #await drift_client.subscribe()

    try:
        await drift_client.add_user(0)
        logger.info("Sub account 0 successfully added")
    except Exception as e:
        logger.error(f"Error subscribing to Drift client: {str(e)}")
        raise e
    try:
        await drift_client.subscribe()
        logger.info("Drift client subscribed successfully")
    except Exception as e:
        logger.error(f"Error subscribing to Drift client: {str(e)}")
        raise e

    MAKE_THE_ORDER = True # Change to true to make an order as well
    SHOW_THE_ORDERS = True
    CANCEL_THE_ORDER = False
    ORDER_ID = 34
    GET_POSITION = False
    GET_ORDER_INFO = False
    GET_MARKET_PRICE = False
    DEPOSIT = False

    if MAKE_THE_ORDER:
        # market_index = 0
        # order_params = OrderParams(
        #     order_type=OrderType.Limit(),
        #     base_asset_amount=drift_client.convert_to_perp_precision(0.01),
        #     market_index=market_index,
        #     direction=PositionDirection.Long(),
        #     price=drift_client.convert_to_price_precision(30000),
        #     post_only=PostOnlyParams.TryPostOnly(),
        # )
        # result = await drift_client.place_perp_order(order_params)
        market_index = 0
        order_params = OrderParams(
            order_type=OrderType.Limit(),
            base_asset_amount=drift_client.convert_to_perp_precision(0.01),
            market_index=0,
            direction=PositionDirection.Long(),
            price=drift_client.convert_to_price_precision(30000), # <--- here
            post_only=PostOnlyParams.TryPostOnly(),
        )

        result = await drift_client.place_perp_order(order_params)
        print("tx_sig", result)

    if SHOW_THE_ORDERS:
        await drift_client.add_user(0)
        user =  drift_client.get_user()
        #open_positions = user.get_user_position(0)
        open_orders = user.get_open_orders()
        await asyncio.sleep(60)
        #logger.info(f"open positions: {open_positions}")
        logger.info(f"next order id: {drift_client.get_user_account(0).next_order_id}")
        logger.info(f"open orders: {open_orders}")

    if CANCEL_THE_ORDER:
        try:
            await drift_client.cancel_order(ORDER_ID)
            logger.info(f"order id {ORDER_ID} cancelled successfully")
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            raise e
    
    if GET_ORDER_INFO:
        try:
            drift_user = drift_client.get_user(0)
            drift_user_account = drift_client.get_user_account(0)
            #orders = drift_user_account.orders
            next_order_id = drift_user_account.next_order_id
            order_info: Optional[Order] = drift_user.get_order(38)
            await asyncio.sleep(60)
            logger.info(f"order id {38} info: {order_info}")
            logger.info(f"next order id: {next_order_id}")
            #logger.info(f"orders from user account: {orders}")
        except Exception as e:
            logger.error(f"Error getting order info: {str(e)}")
            raise e

    if GET_MARKET_PRICE:
        market_price_data = drift_client.get_oracle_price_data_for_perp_market(0)
        logger.info(f"market price data: {market_price_data}")
        logger.info(f"market price: {convert_to_number(market_price_data.price)}")

    if DEPOSIT:
        try:
            #await drift_client.initialize_user()
            await drift_client.deposit(1, 0)
            logger.info(f"deposit of 100 successful")
        except Exception as e:
            logger.error(f"Error depositing: {str(e)}")
            raise e

    # Ensure proper cleanup
    await drift_client.unsubscribe()
    await connection.close()

# if __name__ == "__main__":
#     asyncio.run(test_drift_api())

async def deposit_sol():
    load_dotenv()
    keypath = os.getenv("DRIFT_WALLET_PRIVATE_KEY")
    url = os.getenv("RPC_URL")

    if not keypath:
        raise ValueError("DRIFT_WALLET_PRIVATE_KEY not set in environment variables")
    if not url:
        raise ValueError("RPC_URL not set in environment variables")
    try:
        with open(os.path.expanduser(keypath), "r") as f:
            secret = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Private key file not found at {keypath}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in private key file at {keypath}")

    #keypair = load_keypair(secret)
    keypair = Keypair.from_bytes(bytes(secret))
    wallet = Wallet(keypair)

    #logger.info(f"Using public key: {keypair.pubkey()}")
    connection = AsyncClient(url)
    bulk_account_loader = BulkAccountLoader(connection)

    drift_client = DriftClient(
        connection,
        wallet,
        "devnet", # using devnet 
        tx_params=TxParams(600_000, 100),
        account_subscription=AccountSubscriptionConfig("cached", bulk_account_loader=bulk_account_loader),
        perp_market_indexes=[0],  # Assuming SOL-PERP is market index 0
        spot_market_indexes=[1],  # Assuming SOL is spot market index 1
    )

    try:
        await drift_client.add_user(0)
        logger.info("Sub account 0 successfully added")
    except Exception as e:
        logger.error(f"Error subscribing to Drift client: {str(e)}")
        raise e
    try:
        await drift_client.subscribe()
        logger.info("Drift client subscribed successfully")
    except Exception as e:
        logger.error(f"Error subscribing to Drift client: {str(e)}")
        raise e

    # Get the SOL spot market index (usually 1 for SOL)
    sol_spot_market_index = 1
    pubkey_string = "FVfT5LovFNye8qWKDQJUbVddkaPZPj18WaqxmcfbueaR"
    pubkey = Pubkey.from_string(pubkey_string)
    # Get the user's associated token account for SOL
    user_sol_account = drift_client.get_associated_token_account_public_key(sol_spot_market_index)


    spot_market_index = 1 # SOL 
    amount = drift_client.convert_to_spot_precision(3, spot_market_index) # $100

    tx_sig = await drift_client.deposit(amount, spot_market_index, pubkey)

    print(f"Deposit transaction signature: {tx_sig}")

    await drift_client.unsubscribe()


if __name__ == "__main__":
    asyncio.run(deposit_sol())
