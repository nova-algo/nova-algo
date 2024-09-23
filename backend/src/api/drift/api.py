import os
import json
import logging
import asyncio

from anchorpy import Wallet # type: ignore
from solders.keypair import Keypair # type: ignore
from solana.rpc.async_api import AsyncClient
from driftpy.types import (
    MarketType,
    OrderType,
    OrderParams,
    PositionDirection
)
from driftpy.drift_client import DriftClient
from driftpy.math.perp_position import calculate_entry_price
from driftpy.account_subscription_config import AccountSubscriptionConfig
from driftpy.constants.config import configs
from driftpy.constants.numeric_constants import BASE_PRECISION, PRICE_PRECISION
from driftpy.math.spot_position import (
    get_worst_case_token_amounts,
    is_spot_position_available,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DriftAPI:
    def __init__(self, env="mainnet"):
        self.env = env
        self.drift_client = None

    async def initialize(self, subscription_type="polling"):
        keypath = os.environ.get("DRIFT_WALLET_PRIVATE_KEY")
        with open(os.path.expanduser(keypath), "r") as f:
            secret = json.load(f)

        kp = Keypair.from_bytes(bytes(secret))
        logger.info(f"Using public key: {kp.pubkey()}")

        wallet = Wallet(kp)

        url = configs[self.env].rpc_url
        connection = AsyncClient(url)

        self.drift_client = DriftClient(
            connection,
            wallet,
            self.env,
            account_subscription=AccountSubscriptionConfig(subscription_type),
        )
        
        await self.drift_client.initialize_user()

        # # Add the user with the specified subaccount ID and subscribe to updates
        # await self.drift_client.add_user(subaccount_id)
        # await self.drift_client.subscribe()

    async def get_position_and_maxpos(self, market_index, max_positions):
        user = self.drift_client.get_user()
        positions = []
        open_positions = []

        for position in user.positions:
            if position.market_index == market_index and position.base_asset_amount != 0:
                positions.append(position)
                open_positions.append(position.market)

        num_of_pos = len(open_positions)

        if len(open_positions) > max_positions:
            logger.info(f'We are in {len(open_positions)} positions and max pos is {max_positions}... closing positions')
            for position in open_positions:
                 await self.kill_switch(position.market_index)
        else:
            logger.info(f'We are in {len(open_positions)} positions and max pos is {max_positions}... not closing positions')

        if positions:
            position = positions[0]
            in_pos = True
            size = position.base_asset_amount
            pos_sym = position.market
            entry_px = calculate_entry_price(position)
            pnl_perc = position.unrealized_pnl_percentage * 100
            long = size > 0
        else:
            in_pos = False
            size = 0
            pos_sym = None
            entry_px = 0
            pnl_perc = 0
            long = None

        return positions, in_pos, size, pos_sym, entry_px, pnl_perc, long, num_of_pos

    async def adjust_leverage_size_signal(self, market_index, leverage):
        user = self.drift_client.get_user()
        acct_value = float(user.collateral)
        acct_val95 = acct_value * 0.95

        await self.drift_client.set_leverage(market_index, leverage)

        market = self.drift_client.get_market(market_index)
        price = float(market.oracle_price)

        size = (acct_val95 / price) * leverage
        size = round(size, market.base_precision)

        return leverage, size

    async def cancel_all_orders(self):
        """
        Cancels all open orders using the Drift client.
        
        :param drift_client: The DriftClient instance.

        """

        # market_type = MarketType.Perp()
        # market_index = 0
        # direction = PositionDirection.Long()
        # await drift_client.cancel_orders(market_type, market_index, direction) # cancel bids in perp market 0

        # await drift_client.cancel_orders() # cancels all orders
        
        user = self.drift_client.get_user()
        orders = await asyncio.to_thread(user.get_open_orders)
        #orders = await user.get_open_orders()
        logger.info(f"Open orders: {orders}")
        logger.info('Canceling open orders...')
        for order in orders:
            logger.info(f"Cancelling order {order}")
            await self.drift_client.cancel_order(order.order_id)

    async def limit_order(self, market_index, is_buy, sz, limit_px, reduce_only):
        order_params = OrderParams(
            order_type=OrderType.Limit(),
            market_type=MarketType.Perp(),
            direction=PositionDirection.Long() if is_buy else PositionDirection.Short(),
            base_asset_amount=sz,
            price=limit_px,
            market_index=market_index,
            reduce_only=reduce_only,
        )
        order_result = await self.drift_client.place_order(order_params)

        if is_buy:
            logger.info(f"Limit BUY order placed, resting: {order_result}")
        else:
            logger.info(f"Limit SELL order placed, resting: {order_result}")

        return order_result

    async def kill_switch(self, market_index, market_type):
        """
        Implements a kill switch to close the position when certain conditions are met.
        
        :param market_index: The market index.
        """
        oracle_price_data = self.drift_client.get_oracle_price_data_for_perp_market(market_index)
        position, im_in_pos, pos_size, entry_px, pnl_perc, long = self.get_position(market_index)

        
        position = await self.get_position(market_index)
        im_in_pos = position is not None

        while im_in_pos:
            await self.cancel_all_orders()

            pos_size = abs(position.base_asset_amount)
            long = position.base_asset_amount > 0

            order_params = OrderParams(
                order_type=OrderType.Market(),
                market_type=MarketType.Perp(),
                direction=PositionDirection.Short() if long else PositionDirection.Long(),
                base_asset_amount=pos_size,
                market_index=market_index,
            )
            await self.drift_client.place_order(order_params)

            if long:
                logger.info('Kill switch - SELL TO CLOSE SUBMITTED')
            else:
                logger.info('Kill switch - BUY TO CLOSE SUBMITTED')

            await asyncio.sleep(5)
            position = await self.get_position(market_index)
            im_in_pos = position is not None

        logger.info('Position successfully closed in kill switch')

    async def get_position(self, market_index):
        user = self.drift_client.get_user()
        positions = [position for position in user.positions if position.market_index == market_index]
        return positions[0] if positions else None

    async def get_market_index_by_symbol(self, symbol):
        return await self.drift_client.get_market_index_by_symbol(symbol)

    def get_market(self, market_index):
        return self.drift_client.get_market(market_index)