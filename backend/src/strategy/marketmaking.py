import asyncio
import logging
import time
from typing import Dict, List, Tuple
from decimal import Decimal
import numpy as np
from driftpy.types import OrderType, OrderParams, PositionDirection, MarketType # type: ignore
from driftpy.constants.numeric_constants import BASE_PRECISION, PRICE_PRECISION # type: ignore
from src.api.drift.api import DriftAPI
from src.common.types import MarketMakerConfig, Bot
from typing import Optional

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
        
        self.health_check_interval = 60
        self.last_health_check = 0
        self.is_healthy = True
        self.is_running = False
        
    async def init(self):
        """
        Initialize the market maker by setting up the market index and initial position.
        """
        # Initialize the position
        position = await self.drift_api.get_position(self.market_index)
        if position:
            self.position_size = Decimal(str(position.base_asset_amount)) / BASE_PRECISION
        
        logger.info(f"Initialized market maker for {self.config.symbol} (Market Index: {self.market_index})")
        logger.info(f"Initial position size: {self.position_size}")

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
                await self.manage_inventory()
                await self.place_orders()
                
                # Update last trade price
                market = self.drift_api.get_market(self.market_index)
                self.last_trade_price = Decimal(str(market.oracle_price)) / PRICE_PRECISION
                
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
        Update the local order book with the latest market data.
        """
        # In a real implementation, you would fetch the order book from the API
        # For this example, we'll simulate it with some dummy data
        market = self.drift_api.get_market(self.market_index)
        mid_price = Decimal(str(market.oracle_price)) / PRICE_PRECISION
        
        self.order_book = {
            'bids': [(mid_price - Decimal('0.01') * i, Decimal('10')) for i in range(1, 6)],
            'asks': [(mid_price + Decimal('0.01') * i, Decimal('10')) for i in range(1, 6)]
        }
        
        logger.info(f"Updated order book - Mid price: {mid_price}")

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
            market = self.drift_api.get_market(self.market_index)
            current_price = Decimal(str(market.oracle_price)) / PRICE_PRECISION
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
        market = self.drift_api.get_market(self.market_index)
        mid_price = Decimal(str(market.oracle_price)) / PRICE_PRECISION
        
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
            buy_order = await self.drift_api.drift_client.place_order(buy_params)
            self.current_orders[buy_order.order_id] = buy_params
            
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
            sell_order = await self.drift_api.drift_client.place_order(sell_params)
            self.current_orders[sell_order.order_id] = sell_params
        
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
            
            await self.drift_api.drift_client.place_order(order_params)
            logger.info(f"Placed inventory management order: {'sell' if direction == PositionDirection.Short() else 'buy'} {size}")

    async def update_position(self):
        """
        Update the current position size.
        """
        position = await self.drift_api.get_position(self.market_index)
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