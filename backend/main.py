import asyncio
from decimal import Decimal
import logging
from src.api.drift.api import DriftAPI
from src.strategy.factory import StrategyFactory
#from src.api.drift.error import DriftAPIRequestError
from src.common.types import TrendFollowingConfig
from driftpy.types import MarketType
from dotenv import load_dotenv

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

STRATEGY_CONFIG = TrendFollowingConfig(
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

#@DriftAPIRequestError
async def run_strategy():

    # Load environment variables from .env file
    load_dotenv()

    # Initialize DriftAPI
    drift_api = DriftAPI("devnet")
    await drift_api.initialize(subscription_type="cached")
    logger.info("DriftAPI initialized successfully")

    # Initialize BollingerBandsStrategy using the factory
    strategy = StrategyFactory.create_strategy(STRATEGY_CONFIG, drift_api)
    await strategy.init()
    logger.info(f"{type(strategy).__name__} initialized successfully")

    # Main loop
    while True:
        try:
            await strategy.execute()
            await asyncio.sleep(30)  # Wait for 30 seconds before the next iteration
        except Exception as e:
            logger.error(f"Error in strategy execution: {e}")
            await asyncio.sleep(30)  # Wait for 30 seconds before retrying

async def main():
    try:
        await run_strategy()
    except KeyboardInterrupt:
        logger.info("Program stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main())