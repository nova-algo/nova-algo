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

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Tuple, Union

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
    ModifyOrderParams
)
from driftpy.drift_client import DriftClient
from driftpy.math.perp_position import calculate_entry_price
from driftpy.account_subscription_config import AccountSubscriptionConfig
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

    async def initialize(self, subscription_type: str = "polling") -> None:
        """
        Initializes the connection to the Drift protocol.

        This method sets up the wallet, establishes a connection to the Solana network,
        and initializes the Drift client.

        Args:
            subscription_type (str, optional): The type of subscription for account updates. Defaults to "polling".
        """
        keypath = os.environ.get("DRIFT_WALLET_PRIVATE_KEY")
        with open(os.path.expanduser(keypath), "r") as f:
            secret = json.load(f)

        kp = Keypair.from_bytes(bytes(secret))
        logger.info(f"Using public key: {kp.pubkey()}")

        wallet = Wallet(kp)

        #url = configs[self.env].rpc_url
        # Set the appropriate URL based on the environment (devnet or mainnet)
        # if self.env == "devnet":
        #     url = "https://devnet.helius-rpc.com/?api-key=3a1ca16d-e181-4755-9fe7-eac27579b48c"
        # elif self.env == "mainnet":
        # url = "https://mainnet.helius-rpc.com/?api-key=3a1ca16d-e181-4755-9fe7-eac27579b48c"
        
        url = "https://devnet.helius-rpc.com/?api-key=3a1ca16d-e181-4755-9fe7-eac27579b48c"
        connection = AsyncClient(url)

        self.drift_client = DriftClient(
            connection,
            wallet,
            self.env,
            account_subscription=AccountSubscriptionConfig(subscription_type),
        )
        
        await self.drift_client.initialize_user()

        # Add the user with the specified subaccount ID and subscribe to updates
        # await self.drift_client.add_user(subaccount_id)
        # await self.drift_client.subscribe()
    
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



    async def place_limit_order(self, order_params: OrderParams) -> Optional[str]:
        """
        Places a limit order using the Drift client.

        This method creates and submits a limit order to the Drift exchange using the provided order parameters.
        It supports both perpetual and spot markets, and handles the order placement process accordingly.
        
        :param order_params: The parameters for the limit order.
        :return: The order transaction signature.
        """
        if not isinstance(order_params.market_type, MarketType):
            logger.error("Invalid market type in order_params")
            raise ValueError("Valid MarketType must be specified in order_params")
        if not isinstance(order_params.market_type, MarketType):
            logger.error("Invalid market type in order_params")
            raise ValueError("Valid MarketType must be specified in order_params")

        try:
            if order_params.market_type == MarketType.Perp():
                order_tx_sig = await self.drift_client.place_perp_order(order_params)
            elif order_params.market_type == MarketType.Spot():
                order_tx_sig = await self.drift_client.place_spot_order(order_params)
            else:
                raise ValueError(f"Unsupported market type: {order_params.market_type}")

            direction = "BUY" if order_params.direction == PositionDirection.Long() else "SELL"
            logger.info(f"{order_params.market_type} limit {direction} order placed, order tx: {order_tx_sig}")
            return order_tx_sig

        except Exception as e:
            logger.error(f"Error placing limit order: {str(e)}")
            return None

    def get_position(self, market_index: int, market_type: MarketType) -> Optional[Union[PerpPosition, SpotPosition]]:
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
    
    def get_user_account(self) -> UserAccount:
        """
        Retrieves the user information and stores it in self.user.

        This method fetches the user details from the Drift client, including the user authority
        and other useful information, and assigns it to the self.user attribute.
        """
        try:
            self.user_account = self.drift_client.get_user_account()
            logger.info(f"User retrieved successfully. User ID: {self.user_account.authority}")
            return self.user_account
        except Exception as e:
            logger.error(f"Error retrieving user information: {str(e)}")
            raise  # This re-raises the caught exception

    def get_open_orders(self) -> list[Order]:
        """
        Retrieves the list of user's open orders.

        This method fetches the open orders from the Drift client and returns them as a list.
        
        Returns:
            list: A list of open orders.
        """
        try:
            user = self.drift_client.get_user()
            open_orders = user.get_open_orders()
            logger.info(f"Retrieved {len(open_orders)} open orders.")
            return open_orders
        except Exception as e:
            logger.error(f"Error retrieving open orders: {str(e)}")
            raise  # This re-raises the caught exception
    
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
            

    # trading history “ check my branch in path, I did something there”.
    # funding ( settlement and delivery)



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
    
    