import asyncio
import logging
from src.api.drift import DriftAPI
from src.strategy.bollingerbands import BollingerBandsStrategy
from src.api.drift.error import handle_drift_api_error

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Strategy configuration
STRATEGY_CONFIG = {
    'symbol': 'SOL-PERP',
    'timeframe': '15m',
    'sma_window': 20,
    'lookback_days': 1,
    'size': 1,
    'target': 5,
    'max_loss': -10,
    'leverage': 3,
    'max_positions': 1
}

@handle_drift_api_error
async def run_strategy():
    # Initialize DriftAPI
    drift_api = DriftAPI()
    await drift_api.initialize()
    logger.info("DriftAPI initialized successfully")

    # Initialize BollingerBandsStrategy
    strategy = BollingerBandsStrategy(drift_api, **STRATEGY_CONFIG)
    await strategy.initialize()
    logger.info("BollingerBandsStrategy initialized successfully")

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