import asyncio
import logging
import pandas as pd
import pandas_ta as ta
import ccxt
from src.api.drift.api import DriftAPI
from src.common.types import BollingerBandsConfig, Bot
from typing import Optional

logger = logging.getLogger(__name__)

class BollingerBandsStrategy(Bot):
    def __init__(self, drift_api: DriftAPI, config: BollingerBandsConfig):
        self.drift_api = drift_api
        self.config = config
        self.market_index = self.config.market_indexes[0]  # Assuming we're using the first market index
        self.exchange = ccxt.coinbasepro()

    async def initialize(self):
        #you can also pass market index to the strategy
        #self.market_index = await self.drift_api.get_market_index_by_symbol(self.config.symbol)
        logger.info(f"Initialized strategy for {self.config.symbol} with market index {self.market_index}")

    def fetch_ohlcv(self, limit):
        ohlcv = self.exchange.fetch_ohlcv(self.config.symbol, self.config.timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df

    def calculate_bollinger_bands(self, df):
        #bollinger_bands = ta.bbands(df['close'], length=self.config.sma_window, std=2)
        bollinger_bands = bollinger_bands.iloc[:, [0, 1, 2]]
        bollinger_bands.columns = ['BBL', 'BBM', 'BBU']
        df = pd.concat([df, bollinger_bands], axis=1)
        df['BandWidth'] = df['BBU'] - df['BBL']
        tight_threshold = df['BandWidth'].quantile(0.2)
        wide_threshold = df['BandWidth'].quantile(0.8)
        current_band_width = df['BandWidth'].iloc[-1]
        tight = current_band_width <= tight_threshold
        wide = current_band_width >= wide_threshold
        return df, tight, wide

    async def pnl_close(self):
        logger.info('Entering PNL close check')
        position = await self.drift_api.get_position(self.market_index)

        if position:
            pnl_perc = position.unrealized_pnl_percentage * 100

            if pnl_perc > self.config.target_profit:
                logger.info(f'PNL gain is {pnl_perc}% and target is {self.config.target_profit}%... closing position WIN')
                await self.drift_api.kill_switch(self.market_index)
            elif pnl_perc <= self.config.max_loss:
                logger.info(f'PNL loss is {pnl_perc}% and max loss is {self.config.max_loss}%... closing position LOSS')
                await self.drift_api.kill_switch(self.market_index)
            else:
                logger.info(f'PNL is {pnl_perc}% and within accepted range... not closing position')
        else:
            logger.info('No open position to check for PNL close')

    async def execute(self):
        logger.info(f"Executing strategy for {self.config.symbol}")
        
        positions, in_position, position_size, position_symbol, entry_price, pnl_percent, is_long, num_positions = await self.drift_api.get_position_and_maxpos(self.market_index, self.config.max_positions)

        logger.info(f'Current positions for {self.config.symbol}: {positions}')

        leverage, position_size = await self.drift_api.adjust_leverage_size_signal(self.market_index, self.config.target_leverage)
        position_size *= self.config.size_multiplier

        # Check and close positions based on PNL if in a position
        if in_position:
            await self.drift_api.cancel_all_orders()
            logger.info('In position, checking PNL close')
            await self.pnl_close()
        else:
            logger.info('Not in position, skipping PNL close check')

        # Get current market prices
        market = self.drift_api.get_market(self.market_index)
        bid = float(market.bids[0].price)
        ask = float(market.asks[0].price)
        bid11 = float(market.bids[10].price)
        ask11 = float(market.asks[10].price)

        logger.info(f'Current market prices - Ask: {ask}, Bid: {bid}, Ask11: {ask11}, Bid11: {bid11}')

        # Calculate Bollinger Bands
        df = self.fetch_ohlcv(500)
        # bbdf, bollinger_bands_tight, _ = self.calculate_bollinger_bands(df, length=self.sma_window)
        bbdf, bollinger_bands_tight, _ = self.calculate_bollinger_bands(df)

        logger.info(f'Bollinger bands are tight: {bollinger_bands_tight}')

        # Execute trading logic
        if not in_position and bollinger_bands_tight:
            logger.info('Bollinger bands are tight and we don\'t have a position, entering new position')
            await self.drift_api.cancel_all_orders()

            # Place buy order
            await self.drift_api.limit_order(self.market_index, True, position_size, bid11, False)
            logger.info(f'Placed a BUY order for {position_size} at {bid11}')

            # Place sell order
            await self.drift_api.limit_order(self.market_index, False, position_size, ask11, False)
            logger.info(f'Placed a SELL order for {position_size} at {ask11}')

        elif not bollinger_bands_tight:
            logger.info('Bollinger bands are not tight, cancelling orders and closing positions')
            await self.drift_api.cancel_all_orders()
            for position in positions:
                await self.drift_api.kill_switch(position.market_index)
        else:
            logger.info(f'Current position: {in_position}, Bollinger bands tight: {bollinger_bands_tight}. No action taken.')

        logger.info(f"Finished executing strategy for {self.config.symbol}")
    
    # async def run(self):
    #     await self.initialize()
    #     await self.execute()

    # async def run_loop(self):
    #     while True:
    #         await self.execute()
    #         await asyncio.sleep(self.config.polling_interval)

    
    # async def init(self):
    #     await self.initialize()  # This calls the existing initialize method

    # async def reset(self):
    #     # Implement reset logic here
    #     # For example:
    #     await self.drift_api.cancel_all_orders()
    #     # Reset any strategy-specific state variables

    # async def start_interval_loop(self, interval_ms: Optional[int] = 1000):
    #     while True:
    #         await self.execute()
    #         await asyncio.sleep(interval_ms / 1000)

    # async def health_check(self):
    #     # Implement health check logic here
    #     # For example:
    #     try:
    #         await self.drift_api.get_market(self.market_index)
    #         return True
    #     except Exception as e:
    #         logger.error(f"Health check failed: {e}")
    #         return False
    