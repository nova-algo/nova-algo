
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
        await drift_api.initialize(subscription_type="cached")
        
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

if __name__ == "__main__":
    asyncio.run(run_drift_api_initialize())