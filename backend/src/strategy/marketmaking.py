import asyncio
import logging
import time
from typing import Dict, List, Tuple, Optional
from decimal import Decimal
import numpy as np 
import aiohttp
import requests
import pandas as pd
from io import StringIO
from driftpy.types import OrderType, OrderParams, PositionDirection, MarketType # type: ignore
from driftpy.constants.numeric_constants import BASE_PRECISION, PRICE_PRECISION # type: ignore
from src.api.drift.api import DriftAPI
from src.common.types import MarketAccountType, MarketMakerConfig, Bot, PositionType

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MarketMaker(Bot):
    def __init__(self, drift_api: DriftAPI, config: MarketMakerConfig):
        """
        Initialize the MarketMaker class.

        :param drift_api: Instance of DriftAPI for interacting with the Drift protocol
        :param config: Configuration for the market making strategy
        """
        self.drift_api = drift_api
        self.config = config
        self.market_index = config.market_indexes[0]
        self.current_orders: Dict[int, OrderParams] = {}
        self.position_size = Decimal('0')
        self.last_trade_price = None
        self.order_book: Dict[str, List[Tuple[Decimal, Decimal]]] = {'bids': [], 'asks': []}
        
        self.inventory_extreme = Decimal('50')
        self.max_orders = 8
        
        self.vwap = None
        self.last_price_update = 0
        self.price_update_interval = 60  # Update price every 60 seconds
        self.volatility = Decimal('0.01')  # Initial volatility estimate
        self.volatility_window = 20  # Number of price updates to use for volatility calculation
        self.price_history: List[Decimal] = []
        self.health_check_interval = 60
        self.last_health_check = 0
        self.is_healthy = True
        self.is_running = False
        
    async def init(self):
        """
        Initialize the market maker by setting up the market index and initial position.
        """
        # Initialize the position
        position: Optional[PositionType] = await self.drift_api.get_position(self.market_index, self.config.market_type)
        if position:
            self.position_size = Decimal(str(position.base_asset_amount)) / BASE_PRECISION
        else:
            self.position_size = Decimal('0')
        
        logger.info(f"Initialized market maker for {self.config.symbol} (Market Index: {self.market_index})")
        logger.info(f"Initial position size: {self.position_size}")
        
    async def _skew(self) -> Tuple[float, float]:
        """
        Calculates the skew for bid and ask orders based on the current inventory level and generate skew value.
        """
        skew = self._generate_skew()
        skew = round(skew, 2)
        
        bid_skew = max(0, min(skew, 1))
        ask_skew = max(0, min(-skew, 1))
        
        inventory_delta = self.position_size - self.config.inventory_target
        bid_skew += float(inventory_delta) if inventory_delta < 0 else 0
        ask_skew -= float(inventory_delta) if inventory_delta > 0 else 0
        
        bid_skew = bid_skew if inventory_delta > -self.inventory_extreme else 1
        ask_skew = ask_skew if inventory_delta < +self.inventory_extreme else 1

        if (bid_skew == 1 or ask_skew == 1) and (inventory_delta == 0):
            return 0, 0

        return abs(bid_skew), abs(ask_skew)
        
    def _generate_skew(self) -> float:
        """
        Generate a skew value based on current market conditions and inventory.
        
        :return: A float value between -1 and 1, where:
                - Negative values indicate a bias towards selling
                - Positive values indicate a bias towards buying
                - 0 indicates a neutral stance
        """
        if self.last_trade_price is None or self.vwap is None:
            logger.warning("Not enough data to generate skew. Returning neutral skew.")
            return 0.0

        # 1. Price trend component
        price_trend = (self.last_trade_price - self.vwap) / self.vwap
        price_skew = np.tanh(price_trend * 10)  # Scale and bound the trend

        # 2. Inventory skew component
        inventory_diff = self.position_size - self.config.inventory_target
        max_inventory = self.config.max_position_size
        inventory_skew = -np.tanh(inventory_diff / (max_inventory / 2))  # Negative because we want to reduce inventory

        # 3. Order book imbalance component
        bid_volume = sum(bid[1] for bid in self.order_book['bids'])
        ask_volume = sum(ask[1] for ask in self.order_book['asks'])
        if bid_volume + ask_volume > 0:
            book_imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume)
            book_skew = np.tanh(book_imbalance * 2)
        else:
            book_skew = 0

        # Combine components with weights
        total_skew = (
            0.3 * price_skew +
            0.5 * inventory_skew +
            0.2 * book_skew
        )

        return float(total_skew)

    async def update_vwap(self):
        """Update the Volume Weighted Average Price (VWAP)."""
        current_time = time.time()
        if current_time - self.last_price_update < self.price_update_interval:
            return

        try:
            if self.session is None:
                self.session = aiohttp.ClientSession()
            
            url = 'https://drift-historical-data-v2.s3.eu-west-1.amazonaws.com/program/dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH/user/FrEFAwxdrzHxgc7S4cuFfsfLmcg8pfbxnkCQW83euyCS/tradeRecords/2024/20240929'
            async with self.session.get(url) as response:
                response.raise_for_status()
                content = await response.text()
            
            df = pd.read_csv(StringIO(content))
            df_filtered = df[df['marketIndex'] == self.market_index]
            
            if df_filtered.empty:
                logger.warning(f"No data found for market index {self.market_index}")
                return
            
            df_filtered['volume'] = df_filtered['price'] * df_filtered['size']
            total_volume = df_filtered['volume'].sum()
            self.vwap = df_filtered['volume'].sum() / df_filtered['size'].sum()
            
            self.last_price_update = current_time
            logger.info(f"Updated VWAP: {self.vwap}")
        except Exception as e:
            logger.error(f"Error updating VWAP: {str(e)}")
            
            
    def _prices(self, bid_skew: float, ask_skew: float) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Generates a list of bid and ask prices based on market conditions and skew.
        """
        best_bid, best_ask = self.order_book['bids'][0][0], self.order_book['asks'][0][0]
        spread = self._adjusted_spread()

        if bid_skew >= 1:
            bid_lower = best_bid - (spread * self.max_orders)
            bid_prices = np.linspace(best_bid, bid_lower, self.max_orders)
            return bid_prices, None
        elif ask_skew >= 1:
            ask_upper = best_ask + (spread * self.max_orders)
            ask_prices = np.linspace(best_ask, ask_upper, self.max_orders)
            return None, ask_prices
        elif bid_skew >= ask_skew:
            best_bid = best_ask - spread * 0.33
            best_ask = best_bid + spread * 0.67
        elif bid_skew < ask_skew:
            best_ask = best_bid + spread * 0.33
            best_bid = best_ask - spread * 0.67

        base_range = self.config.volatility_value / 2
        bid_lower = best_bid - (base_range * (1 - bid_skew))
        ask_upper = best_ask + (base_range * (1 - ask_skew))

        bid_prices = np.geomspace(best_bid, bid_lower, self.max_orders // 2)
        ask_prices = np.geomspace(best_ask, ask_upper, self.max_orders // 2)

        return bid_prices, ask_prices
    
    def _sizes(self, bid_skew: float, ask_skew: float) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Calculates order sizes for bid and ask orders, adjusting based on skew and inventory levels.
        """
        if bid_skew >= 1:
            bid_sizes = np.full(
                shape=self.max_orders,
                fill_value=np.median([self.config.min_order_size, self.config.max_order_size / 2])
            )
            return bid_sizes, None
        elif ask_skew >= 1:
            ask_sizes = np.full(
                shape=self.max_orders,
                fill_value=np.median([self.config.min_order_size, self.config.max_order_size / 2])
            )
            return None, ask_sizes

        bid_min = self.config.min_order_size * (1 + bid_skew**0.5)
        bid_upper = self.config.max_order_size * (1 - bid_skew)
        ask_min = self.config.min_order_size * (1 + ask_skew**0.5)
        ask_upper = self.config.max_order_size * (1 - ask_skew)

        bid_sizes = np.geomspace(
            start=bid_min if bid_skew >= ask_skew else self.config.min_order_size,
            stop=bid_upper,
            num=self.max_orders // 2
        )
        ask_sizes = np.geomspace(
            start=ask_min if ask_skew >= bid_skew else self.config.min_order_size,
            stop=ask_upper,
            num=self.max_orders // 2
        )

        return bid_sizes, ask_sizes 
    
    def _adjusted_spread(self) -> Decimal:
        """
        Calculate an adjusted spread based on market conditions and risk factors.
        
        :return: Adjusted spread as a Decimal
        """
        base_spread = self.config.base_spread

        # 1. Volatility adjustment
        volatility_factor = Decimal('1') + (self.volatility / Decimal('0.01'))  # Increase spread by 1% for each 1% of volatility
        
        # 2. Inventory risk adjustment
        inventory_diff = abs(self.position_size - self.config.inventory_target)
        max_inventory = self.config.max_position_size
        inventory_factor = Decimal('1') + (inventory_diff / max_inventory) * Decimal('0.5')  # Max 50% increase for full inventory

        # 3. Market depth adjustment
        if self.order_book['bids'] and self.order_book['asks']:
            bid_volume = sum(bid[1] for bid in self.order_book['bids'][:5])  # Sum volume of top 5 bids
            ask_volume = sum(ask[1] for ask in self.order_book['asks'][:5])  # Sum volume of top 5 asks
            avg_volume = (bid_volume + ask_volume) / 2
            depth_factor = Decimal('1') + (Decimal('100') / (avg_volume + Decimal('1')))  # Increase spread for low liquidity
        else:
            depth_factor = Decimal('1.5')  # Default to 50% increase if order book is empty

        # 4. Time-based adjustment (wider spreads during expected volatile periods)
        current_time = time.localtime()
        if current_time.tm_hour in [14, 15, 16]:  # Assuming market opens at 14:00 UTC
            time_factor = Decimal('1.2')  # 20% wider spreads during first 3 hours of trading
        elif current_time.tm_hour in [21, 22]:  # Assuming market closes at 23:00 UTC
            time_factor = Decimal('1.1')  # 10% wider spreads during last 2 hours of trading
        else:
            time_factor = Decimal('1')

        # Combine all factors
        adjusted_spread = base_spread * volatility_factor * inventory_factor * depth_factor * time_factor

        # Apply minimum and maximum spread limits
        min_spread = self.config.base_spread / 2
        max_spread = self.config.base_spread * 5
        adjusted_spread = max(min_spread, min(adjusted_spread, max_spread))

        logger.info(f"Adjusted spread: {adjusted_spread}")
        return adjusted_spread
    
    async def update_volatility(self):
        """Update the volatility estimate based on recent price history."""
        if self.last_trade_price is None:
            return

        self.price_history.append(self.last_trade_price)
        if len(self.price_history) > self.volatility_window:
            self.price_history.pop(0)

        if len(self.price_history) >= 2:
            returns = [float(price / self.price_history[i - 1] - 1) for i, price in enumerate(self.price_history) if i > 0]
            self.volatility = Decimal(str(np.std(returns) * np.sqrt(len(returns))))
            logger.info(f"Updated volatility estimate: {self.volatility}")
            
            
    async def generate_quotes(self) -> List[Tuple[str, float, float]]:
        """
        Generates a list of market making quotes to be placed on the exchange.
        """
        bid_skew, ask_skew = self._skew()
        bid_prices, ask_prices = self._prices(bid_skew, ask_skew)
        bid_sizes, ask_sizes = self._sizes(bid_skew, ask_skew)

        quotes = []

        if bid_prices is not None and bid_sizes is not None:
            for price, size in zip(bid_prices, bid_sizes):
                quotes.append(("Buy", float(price), float(size)))

        if ask_prices is not None and ask_sizes is not None:
            for price, size in zip(ask_prices, ask_sizes):
                quotes.append(("Sell", float(price), float(size)))

        logger.info(f"Generated {len(quotes)} quotes")
        return quotes
    
    async def place_orders(self):
        """
        Place new orders based on the generated quotes.
        """
        await self.cancel_all_orders()
        quotes = await self.generate_quotes()

        for side, price, size in quotes:
            order_params = OrderParams(
                order_type=OrderType.Limit(),
                market_type=self.config.market_type,
                direction=PositionDirection.Long() if side == "Buy" else PositionDirection.Short(),
                base_asset_amount=int(size * BASE_PRECISION),
                price=int(price * PRICE_PRECISION),
                market_index=self.market_index,
                reduce_only=False
            )
            result = await self.drift_api.place_order_and_get_order_id(order_params)
            if result:
                tx_sig, order_id = result
                if order_id is not None:
                    logger.info(f"Order placed successfully. Tx sig: {tx_sig}, Order ID: {order_id}")
                    self.current_orders[order_id] = order_params
                else:
                    logger.warning(f"Order placed, but couldn't retrieve Order ID. Tx sig: {tx_sig}")
            else:
                logger.error("Failed to place order")

    async def start_interval_loop(self, interval_ms: int = 1000):
        while True:
            try:
                await self.update_order_book()
                await self.update_position()
                await self.place_orders()
                await asyncio.sleep(interval_ms / 1000)
            except Exception as e:
                logger.error(f"An error occurred: {str(e)}")
                await asyncio.sleep(10)
    async def reset(self):
        """
        Reset the market maker state and cancel all existing orders.
        """
        logger.info("Resetting market maker...")
        self.is_running = False

        # Cancel all existing orders
        await self.cancel_all_orders()

        # Reset internal state
        self.current_orders.clear()
        self.position_size = Decimal('0')
        self.last_trade_price = None
        self.order_book = {'bids': [], 'asks': []}
        self.last_health_check = 0
        self.is_healthy = True

        # Re-initialize position
        await self.update_position()

        logger.info("Market maker reset complete.")
        self.is_running = True

    async def start_interval_loop(self, interval_ms: Optional[int] = 1000):
        """
        Start the main loop for the market making strategy.
        """
        self.is_running = True
        while self.is_running:
            try:
                await self.health_check()
                if not self.is_healthy:
                    logger.warning("Health check failed. Attempting to reset...")
                    await self.reset()
                    continue

                await self.update_order_book()
                await self.update_position()
                await self.update_vwap()
                await self.manage_inventory()
                await self.place_orders()
                
                # Update last trade price
                market = self.drift_api.get_market_price_data(self.market_index, self.config.market_type)
                self.last_trade_price = Decimal(str(market.price)) / PRICE_PRECISION
                
                await asyncio.sleep(interval_ms / 1000)
            except Exception as e:
                logger.error(f"An error occurred: {str(e)}")
                await asyncio.sleep(10)  # Wait for 10 seconds before retrying

    async def health_check(self):
        """
        Perform a health check on the market maker.
        """
        current_time = time.time()
        if current_time - self.last_health_check >= self.health_check_interval:
            self.last_health_check = current_time
            
            try:
                await self.drift_api.get_market(self.market_index)
                self.is_healthy = True
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                self.is_healthy = False

    async def update_order_book(self):
        """
        Update the local order book with the latest market data from the API.
        """
        try:
            # Fetch the latest trade records
            url = 'https://drift-historical-data-v2.s3.eu-west-1.amazonaws.com/program/dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH/user/FrEFAwxdrzHxgc7S4cuFfsfLmcg8pfbxnkCQW83euyCS/tradeRecords/2024/20240929'
            response = requests.get(url)
            response.raise_for_status()
            
            # Parse the CSV data
            df = pd.read_csv(StringIO(response.text))
            
            # Filter for the relevant market
            df_filtered = df[df['marketIndex'] == self.market_index]
            
            if df_filtered.empty:
                logger.warning(f"No data found for market index {self.market_index}")
                return
            
            # Get the latest trade price
            latest_trade = df_filtered.iloc[-1]
            self.last_trade_price = Decimal(str(latest_trade['price'])) / PRICE_PRECISION
            
            # Simulate order book based on the latest trade price
            mid_price = self.last_trade_price
            
            self.order_book = {
                'bids': [(mid_price - Decimal('0.01') * i, Decimal('10')) for i in range(1, 6)],
                'asks': [(mid_price + Decimal('0.01') * i, Decimal('10')) for i in range(1, 6)]
            }
            
            logger.info(f"Updated order book - Mid price: {mid_price}")
        except Exception as e:
            logger.error(f"Error updating order book: {str(e)}")


    def calculate_dynamic_spread(self) -> Decimal:
        """
        Calculate the dynamic spread based on current market conditions and inventory.

        :return: The calculated spread as a Decimal
        """
        # Base spread
        spread = self.config.base_spread
        
        # Adjust spread based on inventory risk
        inventory_risk = abs(self.position_size - self.config.inventory_target) / self.config.max_position_size
        spread += self.config.risk_factor * inventory_risk
        
        # Adjust spread based on market volatility
        if self.last_trade_price:
            market_price_data = self.drift_api.get_market_price_data(self.market_index, self.config.market_type)
            current_price = Decimal(str(market_price_data.price)) / PRICE_PRECISION
            price_change = abs(current_price - self.last_trade_price) / self.last_trade_price
            spread += price_change * Decimal('0.5')  # Increase spread by 50% of the price change
        
        logger.info(f"Calculated dynamic spread: {spread}")
        return spread

    def calculate_order_prices(self) -> Tuple[List[Decimal], List[Decimal]]:
        """
        Calculate the prices for buy and sell orders based on the current market and spread.

        :return: Two lists of Decimals, representing buy and sell prices
        """
        spread = self.calculate_dynamic_spread()
        market_price_data = self.drift_api.get_market_price_data(self.market_index, self.config.market_type)
        mid_price = Decimal(str(market_price_data.price)) / PRICE_PRECISION
        half_spread = spread / 2
        buy_prices = [mid_price - half_spread - Decimal('0.01') * i for i in range(self.config.num_levels)]
        sell_prices = [mid_price + half_spread + Decimal('0.01') * i for i in range(self.config.num_levels)]
        
        logger.info(f"Calculated order prices - Buy: {buy_prices}, Sell: {sell_prices}")
        return buy_prices, sell_prices

    async def place_orders(self):
        """
        Place new orders based on the calculated prices and current market conditions.
        """
        await self.cancel_all_orders()
        
        buy_prices, sell_prices = self.calculate_order_prices()
        
        for i in range(self.config.num_levels):
            # Place buy order
            buy_params = OrderParams(
                order_type=OrderType.Limit(),
                market_type=self.config.market_type,
                direction=PositionDirection.Long(),
                base_asset_amount=int(self.config.order_size * BASE_PRECISION),
                price=int(buy_prices[i] * PRICE_PRECISION),
                market_index=self.market_index,
                reduce_only=False
            )
            result = await self.drift_api.place_order_and_get_order_id(buy_params)
            if result:
                tx_sig, order_id = result
                if order_id is not None:
                    print(f"Order placed successfully. Tx sig: {tx_sig}, Order ID: {order_id}")
                else:
                    print(f"Order placed, but couldn't retrieve Order ID. Tx sig: {tx_sig}")
            else:
                print("Failed to place order")

            self.current_orders[order_id] = buy_params
            
            # Place sell order
            sell_params = OrderParams(
                order_type=OrderType.Limit(),
                market_type=self.config.market_type,
                direction=PositionDirection.Short(),
                base_asset_amount=int(self.config.order_size * BASE_PRECISION),
                price=int(sell_prices[i] * PRICE_PRECISION),
                market_index=self.market_index,
                reduce_only=False
            )
            result = await self.drift_api.place_order_and_get_order_id(sell_params)
            
            if result:
                tx_sig, order_id = result
                if order_id is not None:
                    print(f"Order placed successfully. Tx sig: {tx_sig}, Order ID: {order_id}")
                else:
                    print(f"Order placed, but couldn't retrieve Order ID. Tx sig: {tx_sig}")
            else:
                print("Failed to place order")

            self.current_orders[order_id] = sell_params
            #self.current_orders = self.drift_api.get_user_orders_map()
            
        logger.info(f"Placed {len(self.current_orders)} orders")

    async def cancel_all_orders(self):
        """
        Cancel all existing orders.
        """
        await self.drift_api.cancel_all_orders()
        self.current_orders.clear()
        logger.info("Cancelled all existing orders")

    async def manage_inventory(self):
        """
        Manage inventory by adjusting position size towards the target.
        """
        if abs(self.position_size - self.config.inventory_target) > self.config.order_size:
            direction = PositionDirection.Short() if self.position_size > self.config.inventory_target else PositionDirection.Long()
            size = min(abs(self.position_size - self.config.inventory_target), self.config.max_position_size - abs(self.position_size))
            
            order_params = OrderParams(
                order_type=OrderType.Market(),
                market_type=self.config.market_type,
                direction=direction,
                base_asset_amount=int(size * BASE_PRECISION),
                market_index=self.market_index,
                reduce_only=False
            )
            
            await self.drift_api.place_order(order_params)
            logger.info(f"Placed inventory management order: {'sell' if direction == PositionDirection.Short() else 'buy'} {size}")

    async def update_position(self):
        """
        Update the current position size.
        """
        position: PositionType = await self.drift_api.get_position(self.market_index)
        if position:
            self.position_size = Decimal(str(position.base_asset_amount)) / BASE_PRECISION
        else:
            self.position_size = Decimal('0')
        logger.info(f"Updated position size: {self.position_size}")

async def main():
    drift_api = DriftAPI(env="mainnet")
    await drift_api.initialize()
    
    config = MarketMakerConfig(
        bot_id="mm_bot_1",
        strategy_type="market_making",
        market_indexes=[0],  # Assuming SOL-PERP is at index 0
        sub_accounts=[0],  # Assuming using the first sub-account
        market_type=MarketType.Perp(),
        symbol="SOL-PERP",
        timeframe="5m",
        max_position_size=Decimal('100'),
        order_size=Decimal('1'),
        num_levels=5,
        base_spread=Decimal('0.001'),  # 0.1% initial spread
        risk_factor=Decimal('0.005'),
        inventory_target=Decimal('0')
    )
    
    market_maker = MarketMaker(drift_api, config)
    await market_maker.init()
    await market_maker.start_interval_loop()

if __name__ == "__main__":
    asyncio.run(main())