"""
This module provides a high-level API for interacting with the Drift protocol.

It includes functionality for initializing a connection to the Drift protocol,
managing orders, retrieving position information, and performing various trading operations.

Classes:
    DriftAPI: A class that encapsulates methods for interacting with the Drift protocol.

Dependencies:
    - anchorpy
    - solders
    - solana
    - driftpy
"""

from decimal import Decimal
import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Tuple, Union
from dotenv import load_dotenv

from anchorpy import Wallet # type: ignore
from solders.keypair import Keypair # type: ignore
from solders.pubkey import Pubkey # type: ignore
from solana.rpc.async_api import AsyncClient
from driftpy.math.amm import calculate_bid_ask_price
from driftpy.math.market import (calculate_bid_price, calculate_ask_price)
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
    TxParams
)
from driftpy.drift_client import DriftClient
from driftpy.math.perp_position import calculate_entry_price
from driftpy.account_subscription_config import AccountSubscriptionConfig, BulkAccountLoader
from driftpy.constants.config import configs
from driftpy.constants.perp_markets import (devnet_perp_market_configs, mainnet_perp_market_configs)
from driftpy.constants.spot_markets import (devnet_spot_market_configs, mainnet_spot_market_configs)
from driftpy.constants.numeric_constants import BASE_PRECISION, PRICE_PRECISION
from driftpy.math.spot_position import (
    get_worst_case_token_amounts,
    is_spot_position_available,
)

from driftpy.math.perp_position import (
    calculate_position_pnl,
    calculate_entry_price,
    calculate_base_asset_value,
    is_available
)
from driftpy.keypair import load_keypair
from src.common.types import MarketAccountType, PositionType
from solana.rpc import commitment
import pprint

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

class DriftAPI:
    """
    A class that provides methods for interacting with the Drift protocol.

    This class encapsulates the functionality needed to connect to the Drift protocol,
    manage orders, retrieve position information, and perform various trading operations.

    Attributes:
        env (str): The environment to connect to ('mainnet' or 'devnet').
        drift_client (DriftClient): The client instance for interacting with the Drift protocol.
    """

    def __init__(self, env: str = "mainnet"):
        """
        Initializes the DriftAPI instance.

        Args:
            env (str, optional): The environment to connect to. Defaults to "mainnet".
        """
        self.env = env
        self.drift_client = None
        self.user_account: UserAccount | None = None  # Initialize it as None
        self.connection = None
        self.keypair = None
        
    async def initialize(self, subscription_type: str = "cached") -> None:
        """
        Initializes the connection to the Drift protocol.

        This method sets up the wallet, establishes a connection to the Solana network,
        and initializes the Drift client.

        Args:
            subscription_type (str, optional): The type of subscription for account updates. Defaults to "polling".
        """
        
        load_dotenv()
        keypath = os.getenv("DRIFT_WALLET_PRIVATE_KEY")
        url = os.getenv("RPC_URL")
        
        if not keypath:
            raise ValueError("DRIFT_WALLET_PRIVATE_KEY not set in environment variables")
        if not url:
            raise ValueError("RPC_URL not set in environment variables")
        try:
            with open(os.path.expanduser(keypath), "r") as f:
                secret = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Private key file not found at {keypath}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in private key file at {keypath}")
        
        kp = Keypair.from_bytes(bytes(secret))

        wallet = Wallet(kp)

        logger.info(f"Using public key: {kp.pubkey()}")

        self.connection = AsyncClient(url)
        bulk_account_loader = BulkAccountLoader(self.connection)

        self.drift_client = DriftClient(
            self.connection,
            wallet,
            self.env,
            tx_params=TxParams(600_000, 100),
            account_subscription=AccountSubscriptionConfig(subscription_type, bulk_account_loader=bulk_account_loader),
        )
        
        try:
            await self.drift_client.initialize_user()
            logger.info("Drift client user initialized successfully")
        except Exception as e:
            if "custom program error: 0x0" in str(e):
                logger.info("User already initialized. Proceeding with existing user.")
            else:
                raise e

        try:
            await self.drift_client.subscribe()
            logger.info("Drift client subscribed successfully")
        except Exception as e:
            logger.error(f"Error subscribing to Drift client: {str(e)}")
            raise e

        # try:
        #     await self.drift_client.add_user(0)
        #     logger.info("Added a sub account successfully")
        # except Exception as e:
        #     logger.error(f"Error adding sub account: {str(e)}")
        #     raise e

        # Add the user with the specified subaccount ID and subscribe to updates
        # await self.drift_client.add_user(subaccount_id)
        # await self.drift_client.subscribe()
    
    async def close(self):
        """
        Closes the connection and cleans up resources.
        """
        if self.connection:
            await self.connection.close()
            self.connection = None
        if self.drift_client:
            # If DriftClient has a close method, call it here
            # await self.drift_client.close()
            self.drift_client = None
        self.user_account = None
        self.keypair = None
        logger.info("DriftAPI connection closed and resources cleaned up.")

    async def cancel_orders_for_market(self, market_type: MarketType, market_index: int, subaccount_id: Optional[Pubkey] = None):
        """
        Cancels all open orders for a specific market.

        This function retrieves all open orders for the user, filters them by the given market type and index,
        and cancels them if any exist.

        Args:
            market_type (MarketType): The type of the market (e.g., Spot, Perp).
            market_index (int): The index of the market for which to cancel orders.
            subaccount_id (Optional[Pubkey], optional): The subaccount ID. Defaults to None.
        """
        # Get the user object from the Drift client
        user = self.drift_client.get_user()
        
        # Retrieve open orders asynchronously
        open_orders = await asyncio.to_thread(user.get_open_orders)
        logger.info(f"Open orders: {open_orders}")
        
        # Filter orders for the specified market type and index
        matching_orders = [order for order in open_orders if order.market_type == market_type and order.market_index == market_index]
        
        if matching_orders:
            logger.info(f'Canceling {len(matching_orders)} open orders for market type {market_type} and index {market_index}...')
            # Cancel the orders and get the transaction signature
            tx_sig = await self.drift_client.cancel_orders(market_type, market_index, sub_account_id=subaccount_id)
            logger.info(f"Cancelled orders with transaction signature: {tx_sig}")
        else:
            logger.info(f"No open orders to cancel for market type {market_type} and index {market_index}.")

    
    async def cancel_orders_for_market_and_direction(self, market_type: MarketType, market_index: int, direction: PositionDirection, subaccount_id: Optional[Pubkey] = None):
        """
        Cancels all open orders for a specific market and direction.

        This function retrieves all open orders for the user, filters them by the given market type, index, and direction,
        and cancels them if any exist.

        Args:
            market_type (MarketType): The type of the market (e.g., Spot, Perp).
            market_index (int): The index of the market for which to cancel orders.
            direction (PositionDirection): The direction of the orders to cancel (e.g., Long, Short).
            subaccount_id (Optional[Pubkey], optional): The subaccount ID. Defaults to None.
        """
        # Get the user object from the Drift client
        user = self.drift_client.get_user()
        
        # Retrieve open orders asynchronously
        open_orders = await asyncio.to_thread(user.get_open_orders)
        logger.info(f"Open orders: {open_orders}")
        # Filter orders for the specified market type, index, and direction
        matching_orders = [
            order for order in open_orders 
            if order.market_type == market_type 
            and order.market_index == market_index
            and order.direction == direction
        ]
        
        logger.info(f"Matching orders: {matching_orders}")
        
        if matching_orders:
            logger.info(f'Canceling {len(matching_orders)} open orders for market type {market_type} and index {market_index}...')
            # Cancel the orders and get the transaction signature
            tx_sig = await self.drift_client.cancel_orders(market_type, market_index, direction, sub_account_id=subaccount_id)
            logger.info(f"Cancelled orders with transaction signature: {tx_sig}")
        else:
            logger.info(f"No open orders to cancel for market type {market_type} and index {market_index}.")

    
    async def cancel_all_orders(self, subaccount_id: Optional[Pubkey] = None):
        """
        Cancels all open orders for the user.

        Args:
            subaccount_id (Optional[Pubkey], optional): The subaccount ID. Defaults to None.
        """
        # Get the user object from the Drift client
        user = self.drift_client.get_user()
        
        # Retrieve open orders asynchronously
        open_orders = await asyncio.to_thread(user.get_open_orders)
        logger.info(f"Open orders: {open_orders}")
        
        logger.info(f'Canceling {len(open_orders)} open orders...')
        # Cancel the orders and get the transaction signature
        tx_sig = await self.drift_client.cancel_orders(sub_account_id=subaccount_id)
        logger.info(f"Cancelled orders with transaction signature: {tx_sig}")



    async def place_order(self, order_params: OrderParams, subaccount_id: Optional[int] = None) -> Optional[str]:
        """
        Places a limit order using the Drift client.

        This method creates and submits a limit order to the Drift exchange using the provided order parameters.
        It supports both perpetual and spot markets, and handles the order placement process accordingly.
        
        :param order_params: The parameters for the limit order.
        :return: The order transaction signature.
        """
        #self.drift_client.add_user(subaccount_id)
        if not isinstance(order_params.market_type, MarketType):
            logger.error("Invalid market type in order_params")
            raise ValueError("Valid MarketType must be specified in order_params")

        try:
            if order_params.market_type == MarketType.Perp():
                order_tx_sig = await self.drift_client.place_perp_order(order_params, subaccount_id)
            elif order_params.market_type == MarketType.Spot():
                order_tx_sig = await self.drift_client.place_spot_order(order_params, subaccount_id)
            else:
                raise ValueError(f"Unsupported market type: {order_params.market_type}")

            direction = "BUY" if order_params.direction == PositionDirection.Long() else "SELL"
            logger.info(f"{order_params.market_type} limit {direction} order placed, order tx: {order_tx_sig}")
            return str(order_tx_sig)

        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            return None

    def get_position(self, market_index: int, market_type: MarketType) -> Optional[PositionType]:
        """
        Retrieves the position information for the specified market index.
        
        :param market_index: The market index.
        :param market_type: The type of market (Perp or Spot).
        :return: The position information, either PerpPosition or SpotPosition, or None if not found.
        """

        if market_type == MarketType.Perp():
            position = self.drift_client.get_perp_position(market_index)
        else:
            position = self.drift_client.get_spot_position(market_index)

        return position
    
    def get_user_account(self, subaccount_id: Optional[int] = None) -> UserAccount:
        """
        Retrieves the user information and stores it in self.user.

        This method fetches the user details from the Drift client, including the user authority
        and other useful information, and assigns it to the self.user attribute.
        """
        try:
            self.user_account = self.drift_client.get_user_account(subaccount_id)
            logger.info(f"User retrieved successfully. User ID: {self.user_account.authority}")
            return self.user_account
        except Exception as e:
            logger.error(f"Error retrieving user information: {str(e)}")
            raise  # This re-raises the caught exception

    # async def get_open_orders(self, subaccount_id: Optional[int] = None) -> list[Order]:
    #     """
    #     Retrieves the list of user's open orders.

    #     This method fetches the open orders from the Drift client and returns them as a list.
        
    #     Returns:
    #         list: A list of open orders.
    #     """
    #     #self.drift_client.add_user(subaccount_id)
    #     try:
    #         user = self.drift_client.get_user(subaccount_id)
    #         #open_orders = user.get_open_orders()
    #         open_orders = await asyncio.to_thread(user.get_open_orders)
    #         logger.info(f"Retrieved {len(open_orders)} open orders.")
    #         return open_orders
    #     except Exception as e:
    #         logger.error(f"Error retrieving open orders: {str(e)}")
    #         logger.warning("Returning an empty list of orders due to the error.")
    #         return []
    
    def get_open_orders(self, subaccount_id: Optional[int] = None) -> List[Order]:
        """
        Retrieves the list of user's open orders.

        This method fetches the open orders from the Drift client and returns them as a list.
        
        Returns:
            List[Order]: A list of open orders.
        """
        try:
            logger.info(f"Attempting to get user for subaccount_id: {subaccount_id}")
            user = self.drift_client.get_user(subaccount_id)
            logger.info(f"Successfully retrieved user for subaccount_id: {subaccount_id}")

            logger.info("Fetching open orders...")
            #open_orders = await asyncio.to_thread(user.get_open_orders)
            open_orders = user.get_open_orders()

            if open_orders:
                logger.info(f"Retrieved {len(open_orders)} open orders.")
                for order in open_orders:
                    logger.info(f"Order details: {order}")
            else:
                logger.warning("No open orders found.")
            return open_orders
        except Exception as e:
            logger.error(f"Error retrieving open orders: {str(e)}", exc_info=True)
            logger.warning("Returning an empty list of orders due to the error.")
            return []

    def get_market_index_and_type(self, name: str) -> Tuple[int, MarketType]:
        """
        Retrieves market index and type for a given market name.

        Args:
            name (str): The name of the market.

        Returns:
            Tuple[int, MarketType]: A tuple containing the market index and market type.
        """
        return self.drift_client.get_market_index_and_type(name)
    
    async def get_wallet_balance(self) -> int:
        """
        Retrieves the wallet balance.

        This method fetches the wallet balance from the Drift client.

        Returns:
            int: The wallet balance.
        """
        try:
            connection = self.drift_client.connection
            public_key = self.drift_client.wallet.public_key
            response = await connection.get_balance(public_key)
            balance = response.value
            logger.info(f"Wallet balance retrieved successfully: {balance} lamports")
            return balance
        except Exception as e:
            logger.error(f"Error retrieving wallet balance: {str(e)}")
            raise  # This re-raises the caught exception

    
    async def close_position(self, market_index: int, market_type: MarketType) ->  Tuple[Optional[str], Optional[str]]:
        """
        Closes the position for the specified market index.
        
        :param market_index: The market index.
        :param market_type: The type of market (Perp or Spot).
        :return: The transaction signature if successful, None otherwise.
        """
        try:
            position: Union[PerpPosition, SpotPosition] = await self.get_position(market_index, market_type)
            if position is None:
                logger.info(f"No position found for market index {market_index}")
                return None, f"No position found for market index {market_index}"
            
            #tx_sig = None  # Initialize tx_sig to None

            if market_type == MarketType.Perp():
                order_params = OrderParams(
                    order_type=OrderType.Market(),
                    market_type=market_type,
                    direction=PositionDirection.Short() if position.base_asset_amount > 0 else PositionDirection.Long(),
                    base_asset_amount=self.drift_client.convert_to_perp_precision(position.base_asset_amount),
                    market_index=market_index,
                    reduce_only=True
                )
                tx_sig = await self.drift_client.place_perp_order(order_params)
            elif market_type == MarketType.Spot():
                order_params = OrderParams(
                    order_type=OrderType.Market(),
                    market_type=market_type,
                    direction=PositionDirection.Short() if position.scaled_balance > 0 else PositionDirection.Long(),
                    base_asset_amount=self.drift_client.convert_to_spot_precision(position.scaled_balance),
                    market_index=market_index,
                    reduce_only=True
                )
                tx_sig = await self.drift_client.place_spot_order(order_params)
            else:
                logger.error(f"Unsupported market type: {market_type}")
                return None, f"Unsupported market type: {market_type}"

            if tx_sig:
                logger.info(f"Position closed successfully: {tx_sig}")
                return tx_sig, None
            else:
                logger.warning("No transaction signature returned when closing position")
                return None

        except Exception as e:
            logger.error(f"Error closing position: {str(e)}")
            return None, str(e)
    
    
    async def close_all_open_positions(self) -> Dict[int, Dict[str, List[Tuple[Union[PerpPosition, SpotPosition], Optional[str], Optional[str]]]]]:
        """
        Closes all open positions across all accounts and markets (both perp and spot).

        Returns:
            A dictionary with the following structure:
            {
                account_id: {
                    'perp': [(position, tx_sig, error_message), ...],
                    'spot': [(position, tx_sig, error_message), ...]
                },
                ...
            }
            Where tx_sig is the transaction signature if successful, and error_message contains any error that occurred.
        """
        results = {}
        
        all_positions, error = self.get_all_open_positions()
        
        if error:
            logger.error(f"Failed to retrieve open positions: {error}")
            return results

        for account_id, positions in all_positions.items():
            results[account_id] = {'perp': [], 'spot': []}

            # Close perp positions
            for perp_position in positions['perp']:
                tx_sig, error = await self.close_position(account_id, perp_position.market_index, MarketType.Perp())
                key = perp_position.market_index  # or any unique identifier for the position
                results[account_id]['perp'][key] = (perp_position, tx_sig, error)
            # Close spot positions
            for spot_position in positions['spot']:
                tx_sig, error = await self.close_position(account_id, spot_position.market_index, MarketType.Spot())
                key = spot_position.market_index  # or any unique identifier for the position
                results[account_id]['spot'][key] = (spot_position, tx_sig, error)
        return results

    def get_open_perp_positions(self, account_id: int) -> Tuple[List[PerpPosition], Union[str, None]]:
        """
        Get open perp positions for a specific account

        Args:
            account_id (int): The account ID (0 for main account, positive integers for sub-accounts)

        Returns:
            Tuple[List[PerpPosition], Union[str, None]]: A tuple containing the list of open perp positions and an error message (if any)
        """
        try:
            user_account = self.drift_client.get_user_account(account_id if account_id != 0 else None)
            open_positions = []
            for position in user_account.perp_positions:
                if not is_available(position) and position.base_asset_amount != 0:
                    open_positions.append(position)
            return open_positions, None
        except Exception as e:
            error_msg = f"Error retrieving perp positions for account {account_id}: {str(e)}"
            logger.error(error_msg)
            return [], error_msg
     
    def get_open_spot_positions(self, account_id: int) -> Tuple[List[SpotPosition], Union[str, None]]:
        """
        Get open spot positions for a specific account

        Args:
            account_id (int): The account ID (0 for main account, positive integers for sub-accounts)

        Returns:
            Tuple[List[SpotPosition], Union[str, None]]: A tuple containing the list of open spot positions and an error message (if any)
        """
        try:
            user_account = self.drift_client.get_user_account(account_id if account_id != 0 else None)
            open_positions = []
            for position in user_account.spot_positions:
                if not is_spot_position_available(position) and (position.scaled_balance != 0 or position.open_bids != 0 or position.open_asks != 0):
                    open_positions.append(position)
            return open_positions, None
        except Exception as e:
            error_msg = f"Error retrieving spot positions for account {account_id}: {str(e)}"
            logger.error(error_msg)
            return [], error_msg  

    #you might need to rewrite this to and use the drift user class instead
    def get_all_open_positions(self) -> Tuple[Dict[int, Dict[str, List[Union[PerpPosition, SpotPosition]]]], Union[str, None]]:
        """
        Get all open positions (both perp and spot) for the user across main account and all sub-accounts

        Returns:
            Tuple[Dict[int, Dict[str, List[Union[PerpPosition, SpotPosition]]]], Union[str, None]]: 
            A tuple containing:
            1. Dictionary with account_ids as keys (0 for main account, positive integers for sub-accounts), 
               each containing a nested dictionary with 'perp' and 'spot' keys, 
               each containing a list of open positions
            2. An error message if there was a critical error, None otherwise
        """
        all_positions = {}
        account_ids = [0] + self.drift_client.sub_account_ids  # 0 represents the main account

        for account_id in account_ids:
            perp_positions, perp_error = self.get_open_perp_positions(account_id)
            spot_positions, spot_error = self.get_open_spot_positions(account_id)

            if perp_error and spot_error:
                error_msg = f"Failed to retrieve both perp and spot positions for account {account_id}"
                logger.error(error_msg)
                continue

            if perp_positions or spot_positions:
                all_positions[account_id] = {
                    'perp': perp_positions,
                    'spot': spot_positions
                }

        if not all_positions:
            error_msg = "Failed to retrieve any open positions" 
            logger.error(error_msg)
            return {}, error_msg

        return all_positions, None

    async def cancel_order(self, order_id: Optional[int] = None, sub_account_id: Optional[int] = None) -> dict:
        """
        Cancel a specific order or the most recent order if no order_id is provided.

        Args:
            order_id (Optional[int]): The ID of the order to cancel. If None, cancels the most recent order.
            sub_account_id (Optional[int]): The subaccount ID which contains the order. If None, uses the default subaccount.

        Returns:
            dict: A dictionary containing the result of the cancellation attempt.
        """
        try:
            tx_sig = await self.drift_client.cancel_order(order_id, sub_account_id)
            
            return {
                "success": True,
                "message": "Order cancelled successfully",
                "transaction_signature": tx_sig,
                "order_id": order_id,
                "sub_account_id": sub_account_id
            }
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to cancel order: {str(e)}",
                "order_id": order_id,
                "sub_account_id": sub_account_id
            }
    
    #needs to handle both perp and spot and base ammount precision, would refactor
    async def modify_order(self, 
                           order_id: int, 
                           new_price: Optional[float] = None,
                           new_size: Optional[float] = None,
                           sub_account_id: Optional[int] = None) -> dict:
        """
        Modify an existing order.

        Args:
            order_id (int): The ID of the order to modify.
            new_price (Optional[float]): The new price for the order. If None, price remains unchanged.
            new_size (Optional[float]): The new size for the order. If None, size remains unchanged.
            sub_account_id (Optional[int]): The subaccount ID which contains the order. If None, uses the default subaccount.

        Returns:
            dict: A dictionary containing the result of the modification attempt.
        """
        try:
            # Get the existing order
            user = self.drift_client.get_user(sub_account_id)
            existing_order = user.get_order(order_id)
            
            if not existing_order:
                return {
                    "success": False,
                    "message": f"Order with ID {order_id} not found",
                    "order_id": order_id,
                    "sub_account_id": sub_account_id
                }

            # Prepare modification parameters
            modify_params = ModifyOrderParams(
                order_id=order_id,
                price=new_price if new_price is not None else existing_order.price,
                base_asset_amount=new_size if new_size is not None else existing_order.base_asset_amount,
                market_type=existing_order.market_type,
                direction=existing_order.direction,
                market_index=existing_order.market_index,
                reduce_only=existing_order.reduce_only,
                post_only=existing_order.post_only,
                order_type=existing_order.order_type,
            )

            # Modify the order
            tx_sig = await self.drift_client.modify_order(modify_params, sub_account_id)
            
            return {
                "success": True,
                "message": "Order modified successfully",
                "transaction_signature": tx_sig,
                "order_id": order_id,
                "new_price": new_price,
                "new_size": new_size,
                "sub_account_id": sub_account_id
            }
        except Exception as e:
            logger.error(f"Error modifying order: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to modify order: {str(e)}",
                "order_id": order_id,
                "sub_account_id": sub_account_id
            }


    def get_perp_position(self, market_index: int, sub_account_id: Optional[int] = None) -> Optional[PerpPosition]:
        """
        Get the perpetual position for a specific market index.

        Args:
            market_index (int): The index of the market to query.

        Returns:
            Optional[PerpPosition]: The perpetual position if found and not available, otherwise None.
        """
        try:
            drift_user = self.drift_client.get_user(sub_account_id)
            position = drift_user.get_perp_position(market_index)
            return position
        except Exception as e:
            print(f"Error retrieving perpetual position for market index {market_index}: {str(e)}")
            return None
            
    def get_spot_position(self, market_index: int, sub_account_id: Optional[int] = None) -> Optional[SpotPosition]:
        """
        Get the spot position for a specific market index.

        Args:
            market_index (int): The index of the market to query.

        Returns:
            Optional[SpotPosition]: The spot position if found and not available, otherwise None.
        """
        try:
            drift_user = self.drift_client.get_user(sub_account_id)
            position = drift_user.get_spot_position(market_index)
            return position
        except Exception as e:
            print(f"Error retrieving spot position for market index {market_index}: {str(e)}")
            return None

    
    def get_market_price(self, market_index: int, market_type: MarketType) -> Optional[int]:
        """
        Get the current price of a market (perpetual or spot).

        Args:
            market_index (int): The index of the market.
            market_type (MarketType): The type of the market (Perp or Spot).

        Returns:
            Optional[float]: The current price of the market, or None if the price data is unavailable
                            or if there's an issue with the market type.
        """
        try:
            if market_type == MarketType.Perp():
                oracle_price_data = self.get_market_price_data(market_index, MarketType.Perp())
            elif market_type == MarketType.Spot():
                oracle_price_data = self.get_market_price_data(market_index, MarketType.Spot())
            else:
                print(f"Warning: Invalid market type: {market_type}")
                return None
            
            if oracle_price_data is not None:
                return oracle_price_data.price / PRICE_PRECISION
            else:
                return None
        except Exception as e:
            print(f"Error getting market price for index {market_index}, type {market_type}: {str(e)}")
            return None

    def get_market_price_data(self, market_index: int, market_type: MarketType) -> Optional[OraclePriceData]:
        """
        Get the full oracle price data for a market.

        Args:
            market_index (int): The index of the market.
            market_type (MarketType): The type of the market (Perp or Spot).

        Returns:
            Optional[OraclePriceData]: The full oracle price data, or None if unavailable or if there's an error.
        """
        try:
            if market_type == MarketType.Perp():
                return self.drift_client.get_oracle_price_data_for_perp_market(market_index)
            elif market_type == MarketType.Spot():
                return self.drift_client.get_oracle_price_data_for_spot_market(market_index)
            else:
                logger.warning(f"Invalid market type: {market_type}")
                return None
        except Exception as e:
            logger.error(f"Error getting market price data: {e}")
            return None

    
    def get_market(self, market_index: int, market_type: MarketType) -> Optional[MarketAccountType]:
        """
        Get the market account for a given market index and type.

        Args:
            market_index (int): The index of the market.
            market_type (MarketType): The type of the market (Perp or Spot).

        Returns:
            Optional[Union[PerpMarketAccount, SpotMarketAccount]]: The market account, or None if not found.
        """
        if market_type == MarketType.Perp():
            return self.drift_client.get_perp_market_account(market_index)
        elif market_type == MarketType.Spot():
            return self.drift_client.get_spot_market_account(market_index)
        else:
            print(f"Warning: Invalid market type: {market_type}")
            return None
        
    


    async def view_logs(sig: str, connection: AsyncClient):
        connection._commitment = commitment.Confirmed
        logs = ""
        try:
            await connection.confirm_transaction(sig, commitment.Confirmed)
            logs = (await connection.get_transaction(sig))["result"]["meta"]["logMessages"]
        finally:
            connection._commitment = commitment.Processed
        pprint.pprint(logs)
    
    
    #You can cross check the order id gotten from here and comparing it with the nextOrderId you got from the UserAccount before you called this function
    async def place_order_and_get_order_id(self, order_params: OrderParams) -> Optional[Tuple[str, int]]:
        try:
            if order_params.market_type == MarketType.Perp():
                order_tx_sig = await self.drift_client.place_perp_order(order_params)
            elif order_params.market_type == MarketType.Spot():
                order_tx_sig = await self.drift_client.place_spot_order(order_params)
            else:
                logger.warning(f"Unsupported market type: {order_params.market_type}")
                return None

            # Wait for the transaction to be confirmed
            await self.drift_client.connection.confirm_transaction(order_tx_sig)

            # Get the order ID from the transaction logs
            order_id = await self.get_order_id_from_tx_signature(self.drift_client.connection, order_tx_sig)

            if order_id is not None:
                direction = "BUY" if order_params.direction == PositionDirection.Long() else "SELL"
                logger.info(f"{order_params.market_type} limit {direction} order placed, order tx: {order_tx_sig}, order ID: {order_id}")
                return str(order_tx_sig), order_id
            else:
                logger.warning(f"Failed to retrieve order ID from transaction logs for tx: {order_tx_sig}")
                return str(order_tx_sig), None

        except Exception as e:
            logger.error(f"Error placing limit order: {str(e)}")
            return None

    async def get_order_id_from_tx_signature(self, connection: AsyncClient, tx_sig: str) -> Optional[int]:
        try:
            tx_info = await connection.get_transaction(tx_sig, commitment=commitment.Confirmed)
            if tx_info and 'result' in tx_info and 'meta' in tx_info['result']:
                logs = tx_info['result']['meta']['logMessages']
                for log in logs:
                    if "OrderRecord" in log:
                        try:
                            json_str = log[log.index("{"):log.rindex("}")+1]
                            order_record = json.loads(json_str)
                            return order_record['order']['orderId']
                        except (ValueError, KeyError, json.JSONDecodeError) as e:
                            logger.warning(f"Error parsing OrderRecord from log: {str(e)}")
                            continue
            logger.warning(f"No OrderRecord found in transaction logs for tx: {tx_sig}")
            return None
        except Exception as e:
            logger.error(f"Error fetching transaction logs: {str(e)}")
            return None
    
    def get_user_orders_map(self) -> Dict[int, Order]:
        """
        Retrieves all open user orders and maps each order ID to its corresponding Order object.

        Returns:
            Dict[int, Order]: A dictionary where the key is the order ID and the value is the Order object.
        """
        user_account = self.drift_client.get_user_account()
        orders_map = {}

        for order in user_account.orders:
            # Check if the order status is Open
            if "Open" in str(order.status):
                orders_map[order.order_id] = order

        return orders_map

    # Another idea to get order id is you could get the orders of the user before and after the tx and see what the order was
    
    # How do I get an order id after placing an order?
    # The UserAccount that placed the order has a list of orders in UserAccount.orders that has the ids, the user account also has nextOrderId 
    # the order ID will be in the records(order records) that come through after you place it. You also know "ahead of time" what it will
    # be because it is always the user's nextOrderId on their account which monotonically increases, so you could always check if the order
    # from the records is equal to the nextOrderId from the user account and that would be the order id

    # and lastly maybe you can minus one from nextOrderId to get the order id of the order that was just closed, but this should be the least preferred method


    # async def place_limit_order_and_get_order_id(self, order_params: OrderParams) -> Optional[Tuple[str, int]]:
    #         try:
    #             if order_params.market_type == MarketType.Perp():
    #                 order_tx_sig = await self.drift_client.place_perp_order(order_params)
    #             elif order_params.market_type == MarketType.Spot():
    #                 order_tx_sig = await self.drift_client.place_spot_order(order_params)
    #             else:
    #                 raise ValueError(f"Unsupported market type: {order_params.market_type}")

    #             # Wait for the transaction to be confirmed
    #             await self.drift_client.connection.confirm_transaction(order_tx_sig)

    #             # Get the order ID from the transaction logs
    #             order_id = await self.get_order_id_from_tx_signature(self.drift_client.connection, order_tx_sig)

    #             if order_id is not None:
    #                 direction = "BUY" if order_params.direction == PositionDirection.Long() else "SELL"
    #                 logger.info(f"{order_params.market_type} limit {direction} order placed, order tx: {order_tx_sig}, order ID: {order_id}")
    #                 return str(order_tx_sig), order_id
    #             else:
    #                 logger.error(f"Failed to retrieve order ID from transaction logs")
    #                 return None

    #         except Exception as e:
    #             logger.error(f"Error placing limit order: {str(e)}")
    #             return None


    #     async def get_order_id_from_tx_signature(connection: AsyncClient, tx_sig: str) -> Optional[int]:
    #         try:
    #             tx_info = await connection.get_transaction(tx_sig, commitment=commitment.Confirmed)
    #             if tx_info and 'result' in tx_info and 'meta' in tx_info['result']:
    #                 logs = tx_info['result']['meta']['logMessages']
    #                 for log in logs:
    #                     if "OrderRecord" in log:
    #                         order_record = json.loads(log[log.index("{"):])
    #                         return order_record['order']['orderId']
    #             return None
    #         except Exception as e:
    #             print(f"Error fetching transaction logs: {str(e)}")
    #             return None


      
    # async def close_all_positions(self):
    #     """
    #     Closes all open positions for the user across all markets.

    #     :return: A list of transaction signatures for successful closures, empty list if no positions were closed.
    #     """
    #     try:
    #         tx_sigs = []
    #         user_account =  self.drift_client.get_user_account()
            
    #         # Close all perp positions
    #         for perp_position in user_account.perp_positions:
    #             if perp_position.base_asset_amount != 0:
    #                 tx_sig = await self.close_position(perp_position.market_index, MarketType.Perp())
    #                 if tx_sig:
    #                     tx_sigs.append(tx_sig)

    #         # Close all spot positions
    #         for spot_position in user_account.spot_positions:
    #             if spot_position.scaled_balance != 0:
    #                 tx_sig = await self.close_position(spot_position.market_index, MarketType.Spot())
    #                 if tx_sig:
    #                     tx_sigs.append(tx_sig)

    #         if tx_sigs:
    #             logger.info(f"All positions closed successfully. Transaction signatures: {tx_sigs}")
    #         else:
    #             logger.info("No open positions to close.")

    #         return tx_sigs

    #     except Exception as e:
    #         logger.error(f"Error closing all positions: {str(e)}")
    #         return None, str(e)


    
    
    # def get_all_open_positions(self) -> Dict[int, Dict[str, List[Union[PerpPosition, SpotPosition]]]]:
    #     """
    #     Get all open positions (both perp and spot) for the user across main account and all sub-accounts and markets

    #     Returns:
    #         Dict[int, Dict[str, List[Union[PerpPosition, SpotPosition]]]]: 
    #         Dictionary with account_ids as keys (0 for main account, positive integers for sub-accounts), 
    #         each containing a nested dictionary with 'perp' and 'spot' keys, 
    #         each containing a list of open positions

    #     Raises:
    #         Exception: If there's an error retrieving positions for an account
    #     """
    #     all_positions = {}

    #     # List to hold all account IDs (main account + sub-accounts)
    #     account_ids = [0] + self.drift_client.sub_account_ids  # 0 represents the main account

    #     for account_id in account_ids:
    #         try:
    #             if account_id == 0:
    #                 user_account = self.drift_client.get_user_account()  # Main account
    #             else:
    #                 user_account = self.drift_client.get_user_account(account_id)  # Sub-account
                
    #             open_positions = {
    #                 'perp': [],
    #                 'spot': []
    #             }

    #             # Get open perp positions
    #             for position in user_account.perp_positions:
    #                 try:
    #                     if not is_available(position) and position.base_asset_amount != 0:
    #                         open_positions['perp'].append(position)
    #                 except AttributeError as e:
    #                     logger.warning(f"Error processing perp position for account {account_id}: {e}")

    #             # Get open spot positions
    #             for position in user_account.spot_positions:
    #                 try:
    #                     if not is_spot_position_available(position) and (position.scaled_balance != 0 or position.open_bids != 0 or position.open_asks != 0):
    #                         open_positions['spot'].append(position)
    #                 except AttributeError as e:
    #                     logger.warning(f"Error processing spot position for account {account_id}: {e}")

    #             if open_positions['perp'] or open_positions['spot']:
    #                 all_positions[account_id] = open_positions

    #         except Exception as e:
    #             logger.error(f"Error retrieving positions for account {account_id}: {e}")
    #             return None, str(e)

    #     return all_positions


    #from the perp filler example
    
    # async def settle_pnls(self):
    #     logger.info("settle_pnls started, attempting to acquire task_lock...")
    #     now = time.time()

    #     if now < self.last_settle_pnl + (SETTLE_POSITIVE_PNL_COOLDOWN_MS // 1_000):
    #         logger.info("tried to settle positive pnl, but still cooling down...")
    #         return

    #     user = self.drift_client.get_user()
    #     market_indexes = [pos.market_index for pos in user.get_active_perp_positions()]

    #     # If we try to settle pnl on a market with a different status than active it'll fail our ix
    #     # So we filter them out
    #     for market in market_indexes:
    #         perp_market = self.drift_client.get_perp_market_account(market)
    #         if not is_variant(perp_market.status, "Active"):
    #             market_indexes.remove(perp_market.market_index)

    #     if len(market_indexes) < MAX_POSITIONS_PER_USER:
    #         logger.warning(
    #             f"active positions less than max (actual: {len(market_indexes)}, max: {MAX_POSITIONS_PER_USER})"
    #         )
    #         return

    #     async with self.task_lock:
    #         logger.info("settle_pnl acquired task_lock ")
    #         attempt = 0
    #         while attempt < 3:
    #             user = self.drift_client.get_user()
    #             market_indexes = [
    #                 pos.market_index for pos in user.get_active_perp_positions()
    #             ]

    #             if len(market_indexes) <= 1:
    #                 break

    #             chunk_size = len(market_indexes) // 2

    #             for i in range(0, len(market_indexes), chunk_size):
    #                 chunk = market_indexes[i : i + chunk_size]
    #                 logger.critical(f"settle pnl: {attempt} processing chunk: {chunk}")
    #                 try:
    #                     ixs = [set_compute_unit_limit(MAX_CU_PER_TX)]
    #                     users = {
    #                         user.user_public_key: self.drift_client.get_user_account()
    #                     }
    #                     settle_ixs = self.drift_client.get_settle_pnl_ixs(users, chunk)
    #                     ixs += settle_ixs

    #                     sim_result = await simulate_and_get_tx_with_cus(
    #                         ixs,
    #                         self.drift_client,
    #                         self.drift_client.tx_sender,
    #                         self.lookup_tables,
    #                         [],
    #                         SIM_CU_ESTIMATE_MULTIPLIER,
    #                         True,
    #                         self.simulate_tx_for_cu_estimate,
    #                     )

    #                     logger.info(
    #                         f"settle_pnls estimate CUs: {sim_result.cu_estimate}"
    #                     )
    #                     if self.simulate_tx_for_cu_estimate and sim_result.sim_error:
    #                         logger.error(
    #                             f"settle_pnls sim error: {sim_result.sim_error}"
    #                         )
    #                     else:
    #                         sig = await self.drift_client.tx_sender.send(sim_result.tx)
    #                         await asyncio.sleep(0)  # breathe
    #                         logger.success(f"settled pnl, tx sig: {sig.tx_sig}")

    #                 except Exception as e:
    #                     logger.error(
    #                         f"error occurred settling pnl for markets {chunk}: {e}"
    #                     )

    #             attempt += 1

    #         self.last_settle_pnl = now
    #         duration = time.time() - now
    #         logger.success(f"settle_pnls done, took {duration}s")















      
    # async def kill_switch(self, market_index, market_type):
    #     """
    #     Implements a kill switch to close the position when certain conditions are met.
        
    #     :param market_index: The market index.
    #     :param market_type: The type of market (Perp or Spot).
    #     """
    #     oracle_price_data = self.drift_client.get_oracle_price_data_for_perp_market(market_index)
    #     position, im_in_pos, pos_size, entry_px, pnl_perc, long = self.get_position(market_index)

        
    #     position = await self.get_position(market_index)
    #     im_in_pos = position is not None

    #     while im_in_pos:
    #         await self.cancel_all_orders()

    #         pos_size = abs(position.base_asset_amount)
    #         long = position.base_asset_amount > 0

    #         order_params = OrderParams(
    #             order_type=OrderType.Market(),
    #             market_type=MarketType.Perp(),
    #             direction=PositionDirection.Short() if long else PositionDirection.Long(),
    #             base_asset_amount=pos_size,
    #             market_index=market_index,
    #         )
    #         await self.drift_client.place_order(order_params)

    #         if long:
    #             logger.info('Kill switch - SELL TO CLOSE SUBMITTED')
    #         else:
    #             logger.info('Kill switch - BUY TO CLOSE SUBMITTED')

    #         await asyncio.sleep(5)
    #         position = self.drift_client.get_perp_position(market_index)
    #         im_in_pos = position is not None

    #     logger.info('Position successfully closed in kill switch')

    # async def get_position_and_maxpos(self, market_index, max_positions):
    #     user = self.drift_client.get_user()
    #     positions = []
    #     open_positions = []

    #     for position in user.positions:
    #         if position.market_index == market_index and position.base_asset_amount != 0:
    #             positions.append(position)
    #             open_positions.append(position.market)

    #     num_of_pos = len(open_positions)

    #     if len(open_positions) > max_positions:
    #         logger.info(f'We are in {len(open_positions)} positions and max pos is {max_positions}... closing positions')
    #         for position in open_positions:
    #              await self.kill_switch(position.market_index)
    #     else:
    #         logger.info(f'We are in {len(open_positions)} positions and max pos is {max_positions}... not closing positions')

    #     if positions:
    #         position = positions[0]
    #         in_pos = True
    #         size = position.base_asset_amount
    #         pos_sym = position.market
    #         entry_px = calculate_entry_price(position)
    #         pnl_perc = position.unrealized_pnl_percentage * 100
    #         long = size > 0
    #     else:
    #         in_pos = False
    #         size = 0
    #         pos_sym = None
    #         entry_px = 0
    #         pnl_perc = 0
    #         long = None

    #     return positions, in_pos, size, pos_sym, entry_px, pnl_perc, long, num_of_pos
    
    