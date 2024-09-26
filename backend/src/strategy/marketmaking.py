import asyncio
import logging
import os
import time
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv # type: ignore

from src.api.drift.api import DriftAPI
from driftpy.types import MarketType, OrderType, OrderParams, PositionDirection # type: ignore
from driftpy.constants.numeric_constants import BASE_PRECISION, PRICE_PRECISION # type: ignore

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MarketMakingStrategy:
    def __init__(self, 
                drift_api: DriftAPI, 
                market_symbol: str,
                sub_account_id: int,
                max_position_size: Decimal,
                target_spread: Decimal,
                order_size: Decimal,
                update_interval: float,
                volatility_threshold: Decimal):
        """
        Initialize the Market Making Strategy.

        :param drift_api: The DriftAPI instance for interacting with the Drift protocol
        :param market_symbol: The symbol of the market (e.g., 'SOL-PERP')
        :param sub_account_id: The sub-account ID to use for trading
        :param max_position_size: Maximum allowed position size
        :param target_spread: Target spread as a decimal (e.g., 0.002 for 0.2%)
        :param order_size: Size of each order
        :param update_interval: Time between order updates in seconds
        :param volatility_threshold: Threshold for considering the market volatile
        """
        self.drift_api = drift_api
        self.market_symbol = market_symbol
        self.sub_account_id = sub_account_id
        self.max_position_size = max_position_size
        self.target_spread = target_spread
        self.order_size = order_size
        self.update_interval = update_interval
        self.volatility_threshold = volatility_threshold

        self.market_index = 0 #[0]  is SOL-PERP
        self.market_type = 0 #[0]  is SOL-PERP
        self.last_update_time = 0
        self.last_oracle_price = Decimal(0)
        self.current_position = Decimal(0)
        self.open_orders: Dict[str, OrderParams] = {}

        self.health_check_interval = 60  # seconds
        self.last_health_check = 0
        self.is_healthy = True

    async def initialize(self):
        """
        Initialize the market maker by setting up the market index and type.
        """
        self.market_index = await self.drift_api.get_market_index_by_symbol(self.market_symbol)
        market = self.drift_api.get_market(self.market_index)
        self.market_type = market.market_type
        logger.info(f"Initialized market making for {self.market_symbol} (index: {self.market_index}, type: {self.market_type})")

    async def run(self):
        """
        Main loop for the market maker. Continuously update orders and perform health checks.
        """
        while True:
            try:
                await self.update_orders()
                await self.perform_health_check()
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                self.is_healthy = False
                await asyncio.sleep(5)  # Wait before retrying

    async def update_orders(self):
        """
        Update the market maker's orders based on current market conditions and position.
        """
        oracle_price, best_bid, best_ask = await self.get_market_data()
        bid_price, ask_price = self.calculate_order_prices(oracle_price)
        
        current_position, _, _, _, _, _ = await self.drift_api.get_position_and_maxpos(self.market_index, 1)
        
        if self.is_market_volatile(oracle_price):
            logger.info("Market is volatile. Adjusting orders.")
            # Implement logic for handling volatile markets

        bid_size, ask_size = self.adjust_position(oracle_price)

        await self.drift_api.cancel_all_orders()

        if bid_size > 0:
            await self.place_order(True, bid_price, bid_size)
        if ask_size > 0:
            await self.place_order(False, ask_price, ask_size)

    async def perform_health_check(self):
        """
        Perform a health check on the market maker.
        """
        current_time = time.time()
        if current_time - self.last_health_check >= self.health_check_interval:
            self.last_health_check = current_time
            
            try:
                await self.get_market_data()
                self.is_healthy = True
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                self.is_healthy = False

    async def get_market_data(self) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Fetch current market data including oracle price, bid, and ask prices.

        :return: Tuple of (oracle_price, best_bid, best_ask)
        """
        market = self.drift_api.get_market(self.market_index)
        oracle_price = Decimal(market.oracle_price) / PRICE_PRECISION
        best_bid = Decimal(market.amm.bid_price) / PRICE_PRECISION
        best_ask = Decimal(market.amm.ask_price) / PRICE_PRECISION
        return oracle_price, best_bid, best_ask

    def calculate_order_prices(self, oracle_price: Decimal) -> Tuple[Decimal, Decimal]:
        """
        Calculate bid and ask prices based on the oracle price and target spread.

        :param oracle_price: Current oracle price
        :return: Tuple of (bid_price, ask_price)
        """
        half_spread = self.target_spread / 2
        bid_price = oracle_price * (1 - half_spread)
        ask_price = oracle_price * (1 + half_spread)
        return bid_price, ask_price

    def is_market_volatile(self, oracle_price: Decimal) -> bool:
        """
        Determine if the market is currently volatile.

        :param oracle_price: Current oracle price
        :return: True if the market is volatile, False otherwise
        """
        if self.last_oracle_price == Decimal(0):
            self.last_oracle_price = oracle_price
            return False

        price_change = abs(oracle_price - self.last_oracle_price) / self.last_oracle_price
        self.last_oracle_price = oracle_price
        return price_change > self.volatility_threshold

    async def place_order(self, is_buy: bool, price: Decimal, size: Decimal) -> Optional[str]:
        """
        Place a new order on the Drift exchange.

        :param is_buy: True for buy order, False for sell order
        :param price: Order price
        :param size: Order size
        :return: Order ID if successful, None otherwise
        """
        return await self.drift_api.limit_order(
            self.market_index,
            is_buy,
            int(size * BASE_PRECISION),
            int(price * PRICE_PRECISION),
            False  # reduce_only
        )

    def adjust_position(self, oracle_price: Decimal) -> Tuple[Decimal, Decimal]:
        """
        Adjust the current position based on risk management rules.

        :param oracle_price: Current oracle price
        :return: Tuple of (bid_size, ask_size) to maintain or adjust the position
        """
        # Implement position adjustment logic here
        # This is a placeholder implementation
        available_bid_size = (self.max_position_size - self.current_position) / 2
        available_ask_size = (self.max_position_size + self.current_position) / 2
        
        bid_size = min(self.order_size, available_bid_size)
        ask_size = min(self.order_size, available_ask_size)
        
        return bid_size, ask_size

# Main execution
async def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize DriftAPI
    drift_api = DriftAPI(env="mainnet")
    await drift_api.initialize(subscription_type="websocket")

    # Initialize and run the market maker
    market_maker = MarketMakingStrategy(
        drift_api=drift_api,
        market_symbol="SOL-PERP",
        sub_account_id=0,
        max_position_size=Decimal("10"),  # 10 SOL max position
        target_spread=Decimal("0.002"),  # 0.2% spread
        order_size=Decimal("0.1"),  # 0.1 SOL per order
        update_interval=5.0,  # Update every 5 seconds
        volatility_threshold=Decimal("0.005")  # 0.5% price change threshold
    )

    await market_maker.initialize()
    await market_maker.run()
