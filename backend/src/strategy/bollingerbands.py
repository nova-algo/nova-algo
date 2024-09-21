import asyncio
import logging
import pandas as pd
import pandas_ta as ta
import ccxt
from api import DriftAPI

logger = logging.getLogger(__name__)

class BollingerBandsStrategy:    
    def __init__(self, drift_api, symbol, timeframe, sma_window, lookback_days, size, target, max_loss, leverage, max_positions):
        self.drift_api = drift_api
        self.symbol = symbol
        self.timeframe = timeframe
        self.sma_window = sma_window
        self.lookback_days = lookback_days
        self.size = size
        self.target = target
        self.max_loss = max_loss
        self.leverage = leverage
        self.max_positions = max_positions
        self.market_index = None
        self.exchange = ccxt.coinbasepro()

    async def initialize(self):
        self.market_index = await self.drift_api.get_market_index_by_symbol(self.symbol)
        logger.info(f"Initialized strategy for {self.symbol} with market index {self.market_index}")

    def fetch_ohlcv(self, limit):
        ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df

    def calculate_bollinger_bands(self, df, length=20, std_dev=2):
        bollinger_bands = ta.bbands(df['close'], length=length, std=std_dev)
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

            if pnl_perc > self.target:
                logger.info(f'PNL gain is {pnl_perc}% and target is {self.target}%... closing position WIN')
                await self.drift_api.kill_switch(self.market_index)
            elif pnl_perc <= self.max_loss:
                logger.info(f'PNL loss is {pnl_perc}% and max loss is {self.max_loss}%... closing position LOSS')
                await self.drift_api.kill_switch(self.market_index)
            else:
                logger.info(f'PNL is {pnl_perc}% and within accepted range... not closing position')
        else:
            logger.info('No open position to check for PNL close')

    async def execute(self):
        logger.info(f"Executing strategy for {self.symbol}")
        
        # Get current position and market state
        positions, in_position, position_size, position_symbol, entry_price, pnl_percent, is_long, num_positions = await self.drift_api.get_position_and_maxpos(self.market_index, self.max_positions)

        logger.info(f'Current positions for {self.symbol}: {positions}')

        # Adjust leverage and calculate position size
        leverage, position_size = await self.drift_api.adjust_leverage_size_signal(self.market_index, self.leverage)
        position_size /= 2  # Adjust position size as needed

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
        bbdf, bollinger_bands_tight, _ = self.calculate_bollinger_bands(df, length=self.sma_window)

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

        logger.info(f"Finished executing strategy for {self.symbol}")
    