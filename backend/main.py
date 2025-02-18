import asyncio
from decimal import Decimal
import logging
from web3 import Web3
from src.api.drift.api import DriftAPI
from src.api.uniswap import UniswapAPI
from src.strategy.factory import StrategyFactory
#from src.api.drift.error import DriftAPIRequestError
from src.common.types import TrendFollowingConfig, BackrunnerConfig
from driftpy.types import MarketType
from dotenv import load_dotenv
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# # Strategy configuration
# STRATEGY_CONFIG = BollingerBandsConfig(
#     bot_id="bollinger_bot_1",
#     strategy_type="bollinger_bands",
#     market_indexes=[0],  # Assuming 0 is the market index for SOL-PERP
#     sub_accounts=[0],
#     market_type=MarketType.Perp(),
#     symbol="SOL-PERP",
#     timeframe="15m",
#     target_leverage=3.0,
#     spread=0.001,
#     max_positions=1,
#     size_multiplier=0.5,
#     sma_window=20,
#     lookback_days=1,
#     max_loss=-10.0,
#     target_profit=5.0
# )

# Add Backrunner Configuration
BACKRUNNER_CONFIG = BackrunnerConfig(
    bot_id="backrunner_1",
    strategy_type="backrunner",
    chain_id=1,  # Ethereum mainnet
    min_profit=Decimal('0.1'),
    max_gas_price=100000000000,
    simulation_timeout=0.25,
    dry_run=True  # Set to False for live trading
)

TREND_FOLLOWING_CONFIG = TrendFollowingConfig(
    bot_id="trend_following_1",
    strategy_type="trend_following",
    market_indexes=[0],  # Assuming 0 is the market index for SOL-PERP
    sub_accounts=[0],
    market_type=MarketType.Perp(),
    symbol="SOLPERP",
    timeframe="15m",
    target_leverage=2.0,
    #spread=0.001,
    exhaustion_swing_length=40,
    smoothing_factor=5,
    threshold_multiplier=1.5,
    atr_length=14,
    alma_offset=0.85,
    alma_sigma=6,
    pyramiding=5,
    position_size=Decimal('0.75'),
    start_date="2024-01-01T00:00:00Z",
    end_date="2024-10-01T00:00:00Z"
)

async def run_backrunner(w3: Web3):
    """Run the backrunner strategy"""
    # Initialize UniswapAPI
    uniswap_api = UniswapAPI(w3)
    
    # Create and initialize backrunner strategy
    backrunner = StrategyFactory.create_strategy(BACKRUNNER_CONFIG, uniswap_api)
    await backrunner.init()
    logger.info("Backrunner strategy initialized successfully")
    
    return backrunner

async def run_trend_following():
    """Run the trend following strategy"""
    # Initialize DriftAPI
    drift_api = DriftAPI("devnet")
    await drift_api.initialize(subscription_type="cached")
    logger.info("DriftAPI initialized successfully")

    # Initialize trend following strategy
    strategy = StrategyFactory.create_strategy(TREND_FOLLOWING_CONFIG, drift_api)
    await strategy.init()
    logger.info(f"{type(strategy).__name__} initialized successfully")
    
    return strategy

async def run_strategies():
    # Load environment variables
    load_dotenv()

    # Initialize Web3
    w3 = Web3(Web3.WebsocketProvider(os.getenv('WS_PROVIDER_URL')))
    
    # Initialize both strategies
    backrunner = await run_backrunner(w3)
    trend_following = await run_trend_following()
    
    # Main loop
    while True:
        try:
            # Run both strategies concurrently
            await asyncio.gather(
                backrunner.execute(),
                trend_following.execute()
            )
            await asyncio.sleep(30)
        except Exception as e:
            logger.error(f"Error in strategy execution: {e}")
            await asyncio.sleep(30)

async def main():
    try:
        await run_strategies()
    except KeyboardInterrupt:
        logger.info("Program stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main())