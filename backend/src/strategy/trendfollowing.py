import logging
import asyncio
from typing import Optional
import pandas as pd
import numpy as np
from src.common.types import MarketAccountType, PositionType, TrendFollowingConfig, Bot
from src.api.drift.api import DriftAPI
from driftpy.constants.numeric_constants import BASE_PRECISION, PRICE_PRECISION, PERCENTAGE_PRECISION
from decimal import Decimal
import ccxt
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
    TxParams,
    PerpMarketAccount,
    SpotMarketAccount,
)
from solders.pubkey import Pubkey # type: ignore
from solana.rpc.async_api import AsyncClient
from driftpy.math.amm import calculate_bid_ask_price
from driftpy.math.conversion import convert_to_number
from driftpy.math.market import (calculate_bid_price, calculate_ask_price)
from spl.token.async_client import AsyncToken
from spl.token.constants import TOKEN_PROGRAM_ID


logger = logging.getLogger(__name__)

class TrendFollowingStrategy(Bot):
    def __init__(self, drift_api: DriftAPI, config: TrendFollowingConfig):
        self.drift_api = drift_api
        self.config = config
        self.market_index = self.config.market_indexes[0]
        self.historical_data = pd.DataFrame()
        self.is_initialized = False

        # Strategy-specific attributes
        self.exhaustion_swing_length = self.config.exhaustion_swing_length
        self.smoothing_factor = self.config.smoothing_factor
        self.threshold_multiplier = self.config.threshold_multiplier
        self.atr_length = self.config.atr_length
        self.alma_offset = self.config.alma_offset
        self.alma_sigma = self.config.alma_sigma
        self.pyramiding = self.config.pyramiding
        
        self.alma = (self.alma_calc, self.historical_data['Close'], self.exhaustion_swing_length, self.alma_offset, self.alma_sigma)
        self.smoothed_alma = (lambda x: pd.Series(x).rolling(self.smoothing_factor).mean(), self.alma)
        self.atr = (lambda x: pd.Series(x).rolling(self.atr_length).mean(), self.historical_data["TR"])
        self.dynamic_threshold = (lambda x: pd.Series(x) * self.threshold_multiplier, self.atr)
        self.upper_band = (lambda x, y: pd.Series(x) + pd.Series(y).rolling(self.exhaustion_swing_length).std() * 1.5, self.smoothed_alma, self.historical_data['Close'])
        self.lower_band = (lambda x, y: pd.Series(x) - pd.Series(y).rolling(self.exhaustion_swing_length).std() * 1.5, self.smoothed_alma, self.historical_data['Close'])

        # # These should be calculated after historical data is available
        # self.alma = None
        # self.smoothed_alma = None
        # self.atr = None
        # self.dynamic_threshold = None
        # self.upper_band = None
        # self.lower_band = None

    async def initialize(self):
        logger.info(f"Initializing TrendFollowingStrategy for {self.config.symbol}")
        self.historical_data = await self.update_historical_data(self.config.symbol, self.config.timeframe, self.config.start_date, self.config.end_date)
        self.update_indicators()
        self.is_initialized = True
        
    def update_indicators(self):
        self.alma = self.alma_calc(self.historical_data['Close'], self.exhaustion_swing_length, self.alma_offset, self.alma_sigma)
        self.smoothed_alma = self.alma.rolling(self.smoothing_factor).mean()
        self.atr = self.historical_data['TR'].rolling(self.atr_length).mean()
        self.dynamic_threshold = self.atr * self.threshold_multiplier
        self.upper_band = self.smoothed_alma + self.historical_data['Close'].rolling(self.exhaustion_swing_length).std() * 1.5
        self.lower_band = self.smoothed_alma - self.historical_data['Close'].rolling(self.exhaustion_swing_length).std() * 1.5 

    # Fetch historical data from Bybit (or another exchange, if you like)
    def update_historical_data(self, symbol, timeframe, start_date, end_date):
        exchange = ccxt.bybit({'enableRateLimit': True})
        
        timeframe_seconds = {
            '1m': 60, '5m': 300, '15m': 900, '30m': 1800,
            '1h': 3600, '4h': 14400, '1d': 86400
        }
        
        all_ohlcv = []
        current_date = pd.Timestamp(start_date).tz_localize(None)
        end_datetime = pd.Timestamp(end_date).tz_localize(None)
        
        while current_date < end_datetime:
            try:
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe, exchange.parse8601(current_date.isoformat()), limit=1000)
                all_ohlcv.extend(ohlcv)
                if len(ohlcv):
                    current_date = pd.Timestamp(ohlcv[-1][0], unit='ms') + pd.Timedelta(seconds=timeframe_seconds[timeframe])
                else:
                    current_date += pd.Timedelta(days=1)
            except Exception as e:
                print(f"Error fetching data for {symbol}: {e}")
                break
        
        df = pd.DataFrame(all_ohlcv, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
        df = df.set_index('Timestamp')
        df['TR'] = self.calculate_true_range(df)
        return df

    def alma_calc(self, price, window, offset, sigma):
        m = np.floor(offset * (window - 1))
        s = window / sigma
        w = np.exp(-((np.arange(window) - m) ** 2) / (2 * s * s))
        w /= w.sum()

        def alma(x):
            return (np.convolve(x, w[::-1], mode='valid'))[0]

        return pd.Series(price).rolling(window).apply(alma, raw=True)

    # Function to calculate True Range (used in ATR)
    def calculate_true_range(self, df):
        df['Previous Close'] = df['Close'].shift(1)
        df['High-Low'] = df['High'] - df['Low']
        df['High-PrevClose'] = abs(df['High'] - df['Previous Close'])
        df['Low-PrevClose'] = abs(df['Low'] - df['Previous Close'])
        df['TR'] = df[['High-Low', 'High-PrevClose', 'Low-PrevClose']].max(axis=1)
        return df['TR']

     # Function to calculate volatility (standard deviation of returns)
    # It isn't required in the grand scheme but it is a nice to have
    def calculate_volatility(df, window=14):
        df['Returns'] = df['Close'].pct_change()
        df['Volatility'] = df['Returns'].rolling(window).std()
        # Return the rolling standard deviation of returns
        
        return df['Volatility']

    async def execute(self):
        if not self.is_initialized:
            logger.warning("Strategy not initialized. Skipping execution.")
            return

        if not await self.health_check():
            logger.warning("Health check failed. Skipping execution.")
            await self.reset()  # Reset the strategy when health check fails
            return

        await self.update_historical_data(self.config.symbol, self.config.timeframe, self.config.start_date, self.config.end_date)
        self.update_indicators()
        
        current_price = self.historical_data['close'].iloc[-1]
        smoothed_alma = self.historical_data['smoothed_alma'].iloc[-1]
        dynamic_threshold = self.historical_data['dynamic_threshold'].iloc[-1]

        buy_signal = current_price > smoothed_alma + dynamic_threshold
        sell_signal = current_price < smoothed_alma - dynamic_threshold

        position: PositionType = await self.drift_api.get_position(self.market_index)
        current_position_size = Decimal(position.base_asset_amount) / BASE_PRECISION if position else Decimal('0')

        user = self.drift_api.drift_client.get_user()
        total_collateral = user.get_total_collateral()
        free_collateral = user.get_free_collateral()

        # Calculate maximum position size based on pyramiding
        max_position_size = self.config.pyramiding * self.config.position_size * total_collateral

        if buy_signal and current_position_size < max_position_size:
            remaining_size = max_position_size - current_position_size
            position_value = min(remaining_size, free_collateral * self.config.position_size)
            if position_value > 0:
                await self.open_position(PositionDirection.Long(), position_value)
        elif sell_signal and current_position_size > -max_position_size:
            remaining_size = max_position_size + current_position_size
            position_value = min(remaining_size, free_collateral * self.config.position_size)
            if position_value > 0:
                await self.open_position(PositionDirection.Short(), position_value)
        else:
            logger.info("No trading signal or maximum positions reached.")

        # Check for position exit
        if (current_position_size > 0 and sell_signal) or (current_position_size < 0 and buy_signal):
            await self.close_position()

        # if buy_signal and current_position_size < self.config.pyramiding:
        #     await self.open_position(PositionDirection.Long())
        # elif sell_signal and current_position_size > -self.config.pyramiding:
        #     await self.open_position(PositionDirection.Short())
        # else:
        #     logger.info("No trading signal or maximum positions reached.")

    async def open_position(self, direction: PositionDirection, position_value: Decimal):
        user = self.drift_api.drift_client.get_user()
        market = self.drift_api.get_market(self.market_index, self.config.market_type)
        market_price_data = self.drift_api.get_market_price_data(self.market_index, self.config.market_type)
        price = Decimal(str(market_price_data.price)) / PRICE_PRECISION

        # Calculate base asset amount using the provided position_value
        base_asset_amount = self.drift_api.drift_client.convert_to_perp_precision(position_value / price)

        # Check if we're adding to an existing position
        current_position: PositionType = await self.drift_api.get_position(self.market_index)
        current_position_size = Decimal(current_position.base_asset_amount) / BASE_PRECISION if current_position else Decimal('0')
        
        # Adjust for pyramiding
        remaining_pyramid_levels = self.config.pyramiding - abs(current_position_size)
        if remaining_pyramid_levels <= 0:
            logger.info("Maximum pyramid levels reached. Not opening new position.")
            return

        # Adjust base_asset_amount for remaining pyramid levels
        base_asset_amount = base_asset_amount * (remaining_pyramid_levels / self.config.pyramiding)

        # Ensure the position doesn't exceed available collateral
        free_collateral = user.get_free_collateral()
        if position_value > free_collateral:
            logger.warning("Desired position exceeds available collateral. Adjusting size.")
            base_asset_amount = self.drift_api.drift_client.convert_to_perp_precision(free_collateral / price)

        order_params = OrderParams(
            order_type=OrderType.Market(),
            market_index=self.market_index,
            direction=direction,
            base_asset_amount=base_asset_amount,
            market_type=self.config.market_type,
            reduce_only=False
        )

        try:
            order_signature = await self.drift_api.place_order(order_params)
            logger.info(f"Opened {direction} position with size {base_asset_amount / BASE_PRECISION} at market price. Signature: {order_signature}")
        except Exception as e:
            logger.error(f"Failed to open position: {e}")

    async def close_position(self):
        position: PositionType = await self.drift_api.get_position(self.market_index)
        if position and position.base_asset_amount != 0:
            direction = PositionDirection.Short() if position.base_asset_amount > 0 else PositionDirection.Long()
            order_params = OrderParams(
                order_type=OrderType.Market(),
                market_index=self.market_index,
                direction=direction,
                base_asset_amount=abs(position.base_asset_amount),
                market_type=self.config.market_type,
                reduce_only=True
            )
            try:
                order_signature = await self.drift_api.place_order(order_params)
                logger.info(f"Closed position. Signature: {order_signature}")
            except Exception as e:
                logger.error(f"Failed to close position: {e}")

    async def reset(self):
        logger.info(f"Resetting TrendFollowingStrategy for {self.config.symbol}")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await self.drift_api.cancel_all_orders()
                
                position: PositionType = await self.drift_api.get_position(self.market_index, self.config.market_type)
                if position and position.base_asset_amount != 0:
                    await self.close_position()
                
                self.historical_data = pd.DataFrame()
                await self.update_historical_data()
                
                # Reset strategy-specific indicators
                self.alma = None
                self.smoothed_alma = None
                self.atr = None
                self.dynamic_threshold = None
                self.upper_band = None
                self.lower_band = None
                
                self.is_initialized = False
                
                logger.info("Strategy reset complete. Re-initializing...")
                await self.initialize()
                return
            except Exception as e:
                logger.error(f"Reset attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    logger.error("Max reset attempts reached. Manual intervention required.")
                    raise

    async def start_interval_loop(self, interval_ms: int = 60000):
        consecutive_failures = 0
        MAX_CONSECUTIVE_FAILURES = 3
        is_running = True
        
        async def shutdown():
            nonlocal is_running
            is_running = False
            logger.info("Shutting down strategy...")
            await self.reset()

        try:
            while is_running:
                if self.is_initialized:
                    try:
                        if await self.health_check():
                            await self.execute()
                            consecutive_failures = 0
                            
                            # Dynamically adjust interval based on market volatility
                            volatility = self.calculate_volatility()
                            #volatility = self.calculate_perp_volatility(market, oracle_price_data) if self.config.market_type == MarketType.Perp() else self.calculate_spot_volatility(market, oracle_price_data)
                            adjusted_interval = max(30000, min(120000, int(interval_ms * volatility)))
                        else:
                            consecutive_failures += 1
                            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                                logger.error(f"Health check failed {MAX_CONSECUTIVE_FAILURES} times in a row. Resetting strategy.")
                                await self.reset()
                                consecutive_failures = 0
                    except Exception as e:
                        logger.error(f"Error during execution: {e}")
                        consecutive_failures += 1
                        if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                            logger.error(f"Execution failed {MAX_CONSECUTIVE_FAILURES} times in a row. Resetting strategy.")
                            await self.reset()
                            consecutive_failures = 0
                
                await asyncio.sleep(adjusted_interval / 1000)
        except asyncio.CancelledError:
            await shutdown()
        finally:
            logger.info("Strategy execution loop ended.")

    async def health_check(self):
        try:
            user = self.drift_api.drift_client.get_user()
            health = await user.get_health()
            
            # Define a minimum health threshold (e.g., 20%)
            MIN_HEALTH_THRESHOLD = 20
            
            if health < MIN_HEALTH_THRESHOLD:
                logger.warning(f"Account health is low: {health}%. Pausing trading.")
                return False
            
            # Check for sufficient free collateral
            free_collateral = user.get_free_collateral()
            if free_collateral <= 0:
                logger.warning("Insufficient free collateral. Pausing trading.")
                return False
            
            # Check if the user is being liquidated
            if user.is_being_liquidated():
                logger.error("Account is being liquidated. Stopping all trading activity.")
                return False
            
            logger.info(f"Health check passed. Account health: {health}%, Free collateral: {free_collateral}")
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
            
    def calculate_volatility(self):
        # market = self.drift_api.get_market(self.market_index, self.config.market_type)
        # if market is None:
        #     logger.warning(f"Could not get market for index {self.market_index} and type {self.config.market_type}")
        #     return 1.0

        oracle_price_data: OraclePriceData = self.drift_api.get_market_price_data(self.market_index, self.config.market_type)

        if self.config.market_type == MarketType.Perp():
            market: PerpMarketAccount = self.drift_api.get_market(self.market_index, self.config.market_type)
            return self.calculate_perp_volatility(market, oracle_price_data)
        elif self.config.market_type == MarketType.Spot():
            market: SpotMarketAccount = self.drift_api.get_market(self.market_index, self.config.market_type)
            return self.calculate_spot_volatility(market, oracle_price_data)
        else:
            logger.warning(f"Unknown market type: {self.config.market_type}")
            return 1.0
            
        
    def calculate_perp_volatility(self, market: PerpMarketAccount, oracle_price_data: OraclePriceData):
        twap_price = market.amm.historical_oracle_data.last_oracle_price_twap5min
        last_price = market.amm.historical_oracle_data.last_oracle_price
        current_price = oracle_price_data.price

        min_denom = min(current_price, last_price, twap_price)

        c_vs_l = abs((current_price - last_price) * PRICE_PRECISION // min_denom)
        c_vs_t = abs((current_price - twap_price) * PRICE_PRECISION // min_denom)

        recent_std = market.amm.oracle_std * PRICE_PRECISION // min_denom

        c_vs_l_percentage = c_vs_l / PERCENTAGE_PRECISION
        c_vs_t_percentage = c_vs_t / PERCENTAGE_PRECISION
        recent_std_percentage = recent_std / PERCENTAGE_PRECISION

        return max(c_vs_l_percentage, c_vs_t_percentage, recent_std_percentage)

    def calculate_spot_volatility(self, market: SpotMarketAccount, oracle_price_data: OraclePriceData):
        twap_price = market.historical_oracle_data.last_oracle_price_twap5min
        last_price = market.historical_oracle_data.last_oracle_price
        current_price = oracle_price_data.price

        min_denom = min(current_price, last_price, twap_price)

        c_vs_l = abs((current_price - last_price) * PRICE_PRECISION // min_denom)
        c_vs_t = abs((current_price - twap_price) * PRICE_PRECISION // min_denom)

        c_vs_l_percentage = c_vs_l / PERCENTAGE_PRECISION
        c_vs_t_percentage = c_vs_t / PERCENTAGE_PRECISION

        return max(c_vs_l_percentage, c_vs_t_percentage)
