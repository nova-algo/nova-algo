"""Kuru DEX action provider using direct contract interactions."""

import json
import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from web3 import Web3
from web3.types import Wei

from coinbase_agentkit.action_providers.action_decorator import create_action
from coinbase_agentkit.action_providers.action_provider import ActionProvider
from coinbase_agentkit.network import Network
from coinbase_agentkit.wallet_providers import EvmWalletProvider

from .schemas import (
    SwapParams, 
    LimitOrderParams, 
    OrderStatusParams, 
    BatchOrderParams, 
    MarginActionParams, 
    OrderbookParams,
    SUPPORTED_MARKETS_LITERAL,
    SUPPORTED_TOKENS_LITERAL,
    SUPPORTED_NETWORKS_LITERAL,
)
from .constants import (
    ERC20_ABI,
    TOKEN_ADDRESSES, 
    MARKET_ADDRESSES,
    DEFAULT_RPC_URLS, 
    KURU_MARKET_ABI, 
    KURU_ROUTER_ABI, 
    KURU_MARGIN_ABI,
    NETWORK_ID_TO_CHAIN_ID,
    SUPPORTED_NETWORKS,
    NATIVE_TOKEN_ADDRESS,
    KURU_CONTRACT_ADDRESSES,
    DEPOSITABLE_TOKENS,
)
from .utils import approve_token, format_amount_from_decimals, format_amount_with_decimals

# Set up logging
logger = logging.getLogger(__name__)

class KuruActionProvider(ActionProvider[EvmWalletProvider]):
    """Provides actions for interacting with Kuru DEX through direct contract calls."""

    def __init__(self, 
                 rpc_url_by_chain_id: Optional[Dict[int, str]] = None, 
                 ws_url: Optional[str] = None,
                 margin_account_by_chain: Optional[Dict[int, str]] = None,
                 kuru_router_addresses: Optional[Dict[int, str]] = None):
        super().__init__("kuru", [])
        
        # Initialize Web3 providers dictionary
        self.web3_providers: Dict[int, Web3] = {}
        
        # Set configuration values
        self.rpc_url_by_chain_id = rpc_url_by_chain_id or DEFAULT_RPC_URLS
        self.ws_url = ws_url
        self.margin_account_by_chain = margin_account_by_chain or {}
        
        # Store Kuru router addresses
        self.kuru_router_addresses = kuru_router_addresses or {
            10143: "0xc816865f172d640d93712C68a7E1F83F3fA63235"  # Example address for Monad Testnet
        }
    
    def supports_network(self, network: Network) -> bool:
        """Check if this provider supports the given network"""
        return network.protocol_family == "evm" and network.network_id in SUPPORTED_NETWORKS
    
    def _initialize_web3(self, chain_id: int) -> bool:
        """Initialize Web3 provider for specified chain if not already done"""
        if chain_id in self.web3_providers:
            return True
            
        rpc_url = self.rpc_url_by_chain_id.get(chain_id)
        if not rpc_url:
            logger.error(f"No RPC URL configured for chain ID {chain_id}")
            return False
            
        try:
            # Create Web3 instance
            self.web3_providers[chain_id] = Web3(Web3.HTTPProvider(rpc_url))
            # Test connection
            if not self.web3_providers[chain_id].is_connected():
                logger.error(f"Failed to connect to RPC endpoint {rpc_url}")
                del self.web3_providers[chain_id]
                return False
            logger.info(f"Successfully connected to RPC for chain ID {chain_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Web3 provider for chain {chain_id}: {str(e)}")
            if chain_id in self.web3_providers:
                del self.web3_providers[chain_id]
            return False
    
    def _get_margin_account(self, chain_id: int) -> str:
        """Get margin account address for the chain"""
        return self.margin_account_by_chain.get(
            chain_id, 
            KURU_CONTRACT_ADDRESSES.get(chain_id, {}).get("MARGIN_ACCOUNT", "")
        )
    
    def _get_contract(self, chain_id: int, address: str, abi: List[Dict[str, Any]]) -> Any:
        """Get a contract instance using Web3"""
        # Initialize Web3 if needed
        if not self._initialize_web3(chain_id):
            raise Exception(f"Failed to initialize Web3 for chain {chain_id}")
        
        # Get Web3 provider
        web3 = self.web3_providers[chain_id]
        
        # Create and return contract instance
        return web3.eth.contract(address=Web3.to_checksum_address(address), abi=abi)
    
    def _get_token_address(self, network_id: str, token_id: str) -> str:
        """Get token address from token ID"""
        if token_id.lower() == "native":
            return NATIVE_TOKEN_ADDRESS
            
        # Get token address from mapping
        try:
            return TOKEN_ADDRESSES[network_id][token_id.lower()]
        except KeyError:
            raise ValueError(f"Unsupported token: {token_id} on network {network_id}")
    
    def _get_market_address(self, network_id: str, market_id: str) -> str:
        """Get market address from market ID"""
        try:
            return MARKET_ADDRESSES[network_id][market_id.lower()]
        except KeyError:
            raise ValueError(f"Unsupported market: {market_id} on network {network_id}")
    
    @create_action(
        name="swap",
        description="""
This tool allows swapping tokens on the Kuru DEX.
It takes:
- from_token: The token to swap from (usdc, usdt, dak, chog, yaki, or native for MON/ETH)
- to_token: The token to swap to (usdc, usdt, dak, chog, yaki, or native for MON/ETH)
- amount_in: The amount of from_token to swap in decimal units
- min_amount_out: (Optional) Minimum amount of to_token to receive
- slippage_percentage: (Optional) Slippage tolerance in percentage (default: 0.5%)
- network_id: (Optional) Network ID (default: monad-testnet)
- market_id: The market to trade on (mon-usdc, dak-mon, chog-mon, yaki-mon)

Example:
- Swap 10 USDC for MON: from_token=usdc, to_token=native, amount_in=10, market_id=mon-usdc

Important notes:
- The amount_in is in decimal units (e.g., 1.5 ETH, not wei)
- Either specify min_amount_out or slippage_percentage, but not both
- Supported tokens: usdc, usdt, dak, chog, yaki, native (for MON/ETH)
- Supported markets: mon-usdc, dak-mon, chog-mon, yaki-mon
""",
        schema=SwapParams
    )
    def swap(self, wallet_provider: EvmWalletProvider, args: Dict[str, Any]) -> str:
        """Swap tokens on Kuru DEX"""
        params = SwapParams(**args)
        network_id = params.network_id
        
        # Get chain id
        chain_id = NETWORK_ID_TO_CHAIN_ID.get(network_id)
        if not chain_id:
            return f"Unsupported network: {network_id}"
        
        # Initialize Web3
        if not self._initialize_web3(chain_id):
            return f"Failed to initialize Web3 for network {network_id}"
        
        try:
            # Get token addresses
            from_token_address = self._get_token_address(network_id, params.from_token)
            to_token_address = self._get_token_address(network_id, params.to_token)
            
            # Get market address
            market_address = self._get_market_address(network_id, params.market_id)
            
            # First approve token spending if not native token
            if from_token_address != NATIVE_TOKEN_ADDRESS:
                amount_wei = Web3.to_wei(float(params.amount_in), 'ether')
                approve_token(
                    wallet_provider=wallet_provider,
                    token_address=from_token_address,
                    spender_address=market_address,
                    amount=amount_wei
                )
            
            # Create a market order
            is_buy = to_token_address == NATIVE_TOKEN_ADDRESS
            tx_hash = self._create_order(
                wallet_provider=wallet_provider,
                chain_id=chain_id,
                market_address=market_address,
                order_type="market",
                side="buy" if is_buy else "sell",
                size=str(params.amount_in),
                min_amount_out=str(params.min_amount_out) if params.min_amount_out else None,
                cloid=f"swap_{network_id}_{params.amount_in}"
            )
            
            # Wait for receipt
            receipt = wallet_provider.wait_for_transaction_receipt(tx_hash)
            
            # Check status
            if receipt['status'] == 1:
                return f"Successfully executed swap of {params.amount_in} {params.from_token} to {params.to_token} on Kuru. Transaction hash: {tx_hash}"
            else:
                return f"Swap transaction failed. Transaction hash: {tx_hash}"
            
        except Exception as e:
            return f"Failed to execute swap: {str(e)}"
    
    def _create_order(self, 
                  wallet_provider: EvmWalletProvider, 
                  chain_id: int,
                  market_address: str, 
                  order_type: str, 
                  side: str, 
                  size: str, 
                  price: Optional[str] = None,
                  min_amount_out: Optional[str] = None,
                  post_only: bool = False,
                  cloid: Optional[str] = None) -> str:
        """Create an order using direct contract interaction"""
        # Get market contract
        market_contract = self._get_contract(chain_id, market_address, KURU_MARKET_ABI)
        
        # Convert size and price to contract format
        size_value = Web3.to_wei(float(size), 'ether')
        
        # Handle limit orders differently from market orders
        if order_type.lower() == "limit":
            # For limit orders, use addBuyOrder or addSellOrder
            price_value = Web3.to_wei(float(price) if price else 0, 'ether')
            
            if side.lower() == "buy":
                # Encode the addBuyOrder function call
                order_data = market_contract.encode_abi(
                    "addBuyOrder",
                    args=[
                        price_value,       # price
                        size_value,        # size
                        post_only          # postOnly (boolean)
                    ]
                )
            else:  # sell
                # Encode the addSellOrder function call
                order_data = market_contract.encode_abi(
                    "addSellOrder",
                    args=[
                        price_value,       # price
                        size_value,        # size
                        post_only          # postOnly (boolean)
                    ]
                )
            
            logger.info(f"Creating limit {side} order: price={price}, size={size}, post_only={post_only}")
        else:  # market orders
            # For market orders, use placeAndExecuteMarketBuy or placeAndExecuteMarketSell
            min_out = Web3.to_wei(float(min_amount_out) if min_amount_out else 0, 'ether')
            
            if side.lower() == "buy":
                # Encode the placeAndExecuteMarketBuy function call
                order_data = market_contract.encode_abi(
                    "placeAndExecuteMarketBuy",
                    args=[
                        size_value,        # quoteSize (amount to spend)
                        min_out,           # minAmountOut
                        False,             # isMargin
                        True               # fillOrKill
                    ]
                )
            else:  # sell
                # Encode the placeAndExecuteMarketSell function call
                order_data = market_contract.encode_abi(
                    "placeAndExecuteMarketSell",
                    args=[
                        size_value,        # size (amount to sell)
                        min_out,           # minAmountOut
                        False,             # isMargin
                        True               # fillOrKill
                    ]
                )
            
            logger.info(f"Creating market {side} order: size={size}, min_out={min_amount_out}")
        
        # Prepare transaction
        tx_params = {
            "to": market_address,
            "data": order_data,
            "value": 0,  # No ETH value sent with tx
            "gas": 500000  # Higher gas limit for safety
        }
        
        # Send transaction using wallet provider
        tx_hash = wallet_provider.send_transaction(tx_params)
        logger.info(f"Order transaction sent: {tx_hash}")
        
        # Return transaction hash
        return tx_hash
    
    def _cancel_order(self, 
                         wallet_provider: EvmWalletProvider,
                         chain_id: int,
                         market_address: str, 
                         order_id: str) -> str:
        """Cancel an order using direct contract interaction"""
        # Get market contract
        market_contract = self._get_contract(chain_id, market_address, KURU_MARKET_ABI)
        
        # Encode the cancelOrder function call
        cancel_order_data = market_contract.encode_abi(
            "cancelOrder",  # Function name as positional argument (not fn_name=)
            args=[order_id]
        )
        
        # Prepare transaction
        tx_params = {
            "to": market_address,
            "data": cancel_order_data,
            "value": 0
        }
        
        # Send transaction using wallet provider
        tx_hash = wallet_provider.send_transaction(tx_params)
        
        # Return transaction hash
        return tx_hash
    
    def _batch_orders(self,
                         wallet_provider: EvmWalletProvider,
                         chain_id: int,
                         market_address: str,
                         orders: List[Dict[str, Any]]) -> str:
        """Submit multiple orders in a batch using direct contract interaction"""
        # Get market contract
        market_contract = self._get_contract(chain_id, market_address, KURU_MARKET_ABI)
        
        # Prepare batch orders
        order_sides = []
        order_prices = []
        order_sizes = []
        order_types = []
        order_post_only = []
        order_min_out = []
        order_cloids = []
        
        for idx, order in enumerate(orders):
            # Determine side
            side_value = 0  # 0 for buy
            if order.get("side", "").lower() == "sell":
                side_value = 1
            order_sides.append(side_value)
            
            # Price
            price = order.get("price", "0")
            order_prices.append(Web3.to_wei(float(price), 'ether'))
            
            # Size
            size = order.get("size", "0")
            order_sizes.append(Web3.to_wei(float(size), 'ether'))
            
            # Order type
            order_type_value = 0  # 0 for limit
            if order.get("order_type", "").lower() == "market":
                order_type_value = 1
            order_types.append(order_type_value)
            
            # Post only
            post_only = 1 if order.get("post_only", False) else 0
            order_post_only.append(post_only)
            
            # Minimum amount out
            min_out = order.get("min_amount_out", "0")
            order_min_out.append(Web3.to_wei(float(min_out), 'ether'))
            
            # Client order ID
            cloid = order.get("cloid", f"batch_{market_address}_{idx}")
            order_cloids.append(cloid)
        
        # Encode the batchOrders function call
        batch_orders_data = market_contract.encode_abi(
            "batchOrders",  # Function name as positional argument (not fn_name=)
            args=[
                order_sides,
                order_prices,
                order_sizes,
                order_types,
                order_post_only,
                order_min_out,
                order_cloids
            ]
        )
        
        # Prepare transaction
        tx_params = {
            "to": market_address,
            "data": batch_orders_data,
            "value": 0
        }
        
        # Send transaction using wallet provider
        tx_hash = wallet_provider.send_transaction(tx_params)
        
        # Return transaction hash
        return tx_hash

    def _deposit_to_margin(self,
                          wallet_provider: EvmWalletProvider,
                          chain_id: int,
                          token_address: str,
                          amount: Union[int, str]) -> str:
        """Deposit tokens to margin account using direct contract interaction
        
        Based on the Kuru TypeScript SDK (https://github.com/Kuru-Labs/kuru-sdk)
        """
        # Get margin account address
        margin_account = self._get_margin_account(chain_id)
        if not margin_account:
            raise ValueError(f"No margin account address configured for chain {chain_id}")
        
        # Convert amount to wei if it's a string
        amount_wei = Web3.to_wei(float(amount), 'ether') if isinstance(amount, str) else amount
        
        # Get user address
        user_address = wallet_provider.get_address()
        
        try:
            # Get margin contract
            margin_contract = self._get_contract(chain_id, margin_account, KURU_MARGIN_ABI)
            
            # Encode the deposit function call with the appropriate parameters
            # According to the ABI, deposit takes (address _user, address _token, uint256 _amount)
            deposit_data = margin_contract.encode_abi(
                "deposit",  # Function name as positional argument (not fn_name=)
                args=[
                    user_address,               # User address (_user)
                    token_address,              # Token address (_token)
                    amount_wei                  # Amount in wei (_amount)
                ]
            )
            
            # Log transaction details for debugging
            logger.info(f"Preparing deposit transaction: to={margin_account}, user={user_address}, token={token_address}, amount={amount_wei}")
            
            # Check if this is native token (ETH/MON)
            if token_address == NATIVE_TOKEN_ADDRESS:
                # For native token, we need to send value with the transaction
                
                # Verify user has enough balance
                native_balance = wallet_provider.get_balance()
                if native_balance < amount_wei:
                    raise ValueError(
                        f"Insufficient native token balance. Requested: {format_amount_with_decimals(amount_wei, 18)} MON, "
                        f"Available: {format_amount_with_decimals(native_balance, 18)} MON"
                    )
                
                tx_params = {
                    "to": margin_account,
                    "data": deposit_data,
                    "value": amount_wei,     # Send ETH/MON with transaction
                    "gas": 500000,           # Higher gas limit for safety
                    "gasPrice": None         # Let wallet provider determine gas price
                }
                logger.info("Sending native token deposit with value field")
            else:
                # For ERC20 tokens - Perform approval first if needed
                try:
                    # Approve margin account to spend tokens
                    approval_receipt = approve_token(
                        wallet_provider=wallet_provider,
                        token_address=token_address,
                        spender_address=margin_account,
                        amount=amount_wei
                    )
                    
                    # Log approval details
                    if approval_receipt:
                        tx_hash = approval_receipt.get("transactionHash", "unknown")
                        logger.info(f"Token approval completed with hash: {tx_hash}")
                    else:
                        logger.info("No approval needed (possibly for native token)")
                    
                    # Check if receipt status is successful
                    if approval_receipt and approval_receipt.get("status") != 1:
                        tx_hash = approval_receipt.get("transactionHash", "unknown")
                        raise Exception(f"Token approval failed: {tx_hash}")
                    
                    logger.info("Token approval confirmed, proceeding with deposit")
                except Exception as e:
                    logger.error(f"Error during token approval: {str(e)}")
                    raise
                
                # Now prepare the deposit transaction
                tx_params = {
                    "to": margin_account,
                    "data": deposit_data,
                    "value": 0,              # No ETH value for ERC20 deposits
                    "gas": 400000            # Gas limit for ERC20 deposit
                }
                logger.info("Sending ERC20 token deposit")
            
            # Send transaction using wallet provider
            tx_hash = wallet_provider.send_transaction(tx_params)
            logger.info(f"Deposit transaction sent: {tx_hash}")
            
            return tx_hash
        except Exception as e:
            logger.error(f"Error in _deposit_to_margin: {str(e)}")
            raise
    
    def _get_margin_balance(self,
                              wallet_provider: EvmWalletProvider,
                              chain_id: int,
                              token_address: str) -> int:
        """Get token balance in margin account"""
        # Get margin account address
        margin_account = self._get_margin_account(chain_id)
        
        # Get margin contract
        margin_contract = self._get_contract(chain_id, margin_account, KURU_MARGIN_ABI)
        
        # Call balanceOf function
        balance = margin_contract.functions.tokenBalances(token_address).call()
        
        return balance

    def _get_orderbook(self,
                          wallet_provider: EvmWalletProvider,
                          chain_id: int,
                          market_address: str) -> Dict[str, Any]:
        """Get orderbook for a market"""
        # Get market contract
        market_contract = self._get_contract(chain_id, market_address, KURU_MARKET_ABI)
        
        # Get bids
        bids = market_contract.functions.getBids().call()
        
        # Get asks
        asks = market_contract.functions.getAsks().call()
        
        # Format orderbook
        formatted_bids = []
        for bid in bids:
            formatted_bids.append({
                "price": Web3.from_wei(bid[0], 'ether'),
                "size": Web3.from_wei(bid[1], 'ether'),
                "id": bid[2]
            })
        
        formatted_asks = []
        for ask in asks:
            formatted_asks.append({
                "price": Web3.from_wei(ask[0], 'ether'),
                "size": Web3.from_wei(ask[1], 'ether'),
                "id": ask[2]
            })
        
        # Return orderbook
        return {
            "bids": formatted_bids,
            "asks": formatted_asks
        }
    
    @create_action(
        name="place-limit-order",
        description="""
This tool allows placing a limit order on the Kuru DEX.
It takes:
- from_token: The token to sell (usdc, usdt, dak, chog, yaki, or native for MON/ETH)
- to_token: The token to buy (usdc, usdt, dak, chog, yaki, or native for MON/ETH)
- amount_in: The amount of from_token to sell in decimal units
- price: The limit price in to_token per from_token
- post_only: (Optional) Whether to make the order post-only
- network_id: (Optional) Network ID (default: monad-testnet)
- market_id: The market to trade on (mon-usdc, dak-mon, chog-mon, yaki-mon)

Example:
- Sell 10 USDC for MON at 0.0005 MON per USDC: from_token=usdc, to_token=native, amount_in=10, price=0.0005, market_id=mon-usdc

Important notes:
- The amount_in is in decimal units (e.g., 10 USDC, not wei)
- Price is expressed in to_token per from_token
- Supported tokens: usdc, usdt, dak, chog, yaki, native (for MON/ETH)
- Supported markets: mon-usdc, dak-mon, chog-mon, yaki-mon
""",
        schema=LimitOrderParams
    )
    def place_limit_order(self, wallet_provider: EvmWalletProvider, args: Dict[str, Any]) -> str:
        """Place a limit order on Kuru DEX"""
        params = LimitOrderParams(**args)
        network_id = params.network_id
        
        # Get chain id
        chain_id = NETWORK_ID_TO_CHAIN_ID.get(network_id)
        if not chain_id:
            return f"Unsupported network: {network_id}"
        
        # Initialize Web3
        if not self._initialize_web3(chain_id):
            return f"Failed to initialize Web3 for network {network_id}"
        
        try:
            # Get token addresses
            from_token_address = self._get_token_address(network_id, params.from_token)
            to_token_address = self._get_token_address(network_id, params.to_token)
            
            # Get market address
            market_address = self._get_market_address(network_id, params.market_id)
            
            # First approve token spending if not native token
            if from_token_address != NATIVE_TOKEN_ADDRESS:
                amount_wei = Web3.to_wei(float(params.amount_in), 'ether')
                approve_token(
                    wallet_provider=wallet_provider,
                    token_address=from_token_address,
                    spender_address=market_address,
                    amount=amount_wei
                )
            
            # Create a limit order
            is_buy = to_token_address == NATIVE_TOKEN_ADDRESS
            tx_hash = self._create_order(
                wallet_provider=wallet_provider,
                chain_id=chain_id,
                market_address=market_address,
                order_type="limit",
                side="buy" if is_buy else "sell",
                size=str(params.amount_in),
                price=str(params.price),
                post_only=params.post_only,
                cloid=f"limit_{network_id}_{params.amount_in}_{params.price}"
            )
            
            # Wait for receipt
            receipt = wallet_provider.wait_for_transaction_receipt(tx_hash)
            
            # Check status
            if receipt['status'] == 1:
                return f"Successfully placed limit order to {'buy' if is_buy else 'sell'} {params.amount_in} {params.from_token} at price {params.price}. Transaction hash: {tx_hash}"
            else:
                return f"Limit order transaction failed. Transaction hash: {tx_hash}"
            
        except Exception as e:
            return f"Failed to place limit order: {str(e)}"
    
    @create_action(
        name="cancel-order",
        description="""
This tool allows cancelling an existing order on Kuru DEX.
It takes:
- order_id: The client order ID (cloid) of the order to cancel
- market_id: The market to trade on (mon-usdc, dak-mon, chog-mon, yaki-mon)
- network_id: (Optional) Network ID (default: monad-testnet)

Example:
- Cancel order with client ID 'limit_mon-usdc_10_0.0005'

Important notes:
- You can only cancel orders that you created
- Orders that are already filled cannot be cancelled
- Supported markets: mon-usdc, dak-mon, chog-mon, yaki-mon
""",
        schema=OrderStatusParams
    )
    def cancel_order(self, wallet_provider: EvmWalletProvider, args: Dict[str, Any]) -> str:
        """Cancel an existing order on Kuru DEX"""
        params = OrderStatusParams(**args)
        network_id = params.network_id
        
        # Get chain id
        chain_id = NETWORK_ID_TO_CHAIN_ID.get(network_id)
        if not chain_id:
            return f"Unsupported network: {network_id}"
        
        # Initialize Web3
        if not self._initialize_web3(chain_id):
            return f"Failed to initialize Web3 for network {network_id}"
        
        try:
            # Cancel the order
            tx_hash = self._cancel_order(
                wallet_provider=wallet_provider,
                chain_id=chain_id,
                market_address=params.market_id,
                order_id=params.order_id
            )
            
            # Wait for receipt
            receipt = wallet_provider.wait_for_transaction_receipt(tx_hash)
            
            # Check status
            if receipt['status'] == 1:
                return f"Successfully cancelled order {params.order_id} on Kuru. Transaction hash: {tx_hash}"
            else:
                return f"Order cancellation failed. Transaction hash: {tx_hash}"
            
        except Exception as e:
            return f"Failed to cancel order: {str(e)}"
        
    @create_action(
        name="batch-orders",
        description="""
This tool allows submitting multiple orders in a single transaction.
It takes:
- orders: A list of order specifications, each containing:
  - order_type: 'limit' or 'market'
  - side: 'buy' or 'sell'
  - price: Required for limit orders
  - size: Amount to trade
  - min_amount_out: (Optional) For market orders
  - post_only: (Optional) For limit orders
  - cloid: (Optional) Client order ID
- market_id: The market to trade on (mon-usdc, dak-mon, chog-mon, yaki-mon)
- network_id: (Optional) Network ID (default: monad-testnet)

Example:
- Submit multiple orders: [{"order_type":"limit","side":"buy","price":"0.00000002","size":"10000"},{"order_type":"limit","side":"sell","price":"0.00000003","size":"10000"}]

Important notes:
- Batch orders are more gas efficient than individual orders
- All orders in a batch must be for the same market
- Supported markets: mon-usdc, dak-mon, chog-mon, yaki-mon
""",
        schema=BatchOrderParams
    )
    def batch_orders(self, wallet_provider: EvmWalletProvider, args: Dict[str, Any]) -> str:
        """Submit multiple orders in a single transaction"""
        params = BatchOrderParams(**args)
        network_id = params.network_id
        
        # Get chain id
        chain_id = NETWORK_ID_TO_CHAIN_ID.get(network_id)
        if not chain_id:
            return f"Unsupported network: {network_id}"
        
        # Initialize Web3
        if not self._initialize_web3(chain_id):
            return f"Failed to initialize Web3 for network {network_id}"
        
        try:
            # Execute batch orders
            tx_hash = self._batch_orders(
                wallet_provider=wallet_provider,
                chain_id=chain_id,
                market_address=params.market_id,
                orders=params.orders
            )
            
            # Wait for receipt
            receipt = wallet_provider.wait_for_transaction_receipt(tx_hash)
            
            # Check status
            if receipt['status'] == 1:
                return f"Successfully submitted batch of {len(params.orders)} orders. Transaction hash: {tx_hash}"
            else:
                return f"Batch order transaction failed. Transaction hash: {tx_hash}"
            
        except Exception as e:
            return f"Failed to submit batch orders: {str(e)}"
    
    @create_action(
        name="deposit-margin",
        description="""
This tool allows depositing MON to your Kuru margin account on Monad testnet.
It takes:
- amount: The amount of MON to deposit in decimal units
- network_id: (Optional) Network ID (default: monad-testnet)

Example:
- Deposit 10 MON: amount=10

Important notes:
- Only native MON can be deposited on Monad testnet
- No other tokens are supported for deposits
""",
        schema=MarginActionParams
    )
    def deposit_margin(self, wallet_provider: EvmWalletProvider, args: Dict[str, Any]) -> str:
        """Deposit assets to a Kuru margin account"""
        try:
            params = MarginActionParams(**args)
            network_id = params.network_id
            token_id = params.token_id
            
            # Check if token is depositable for the network (schema validation should handle this,
            # but we double-check here for extra safety)
            if network_id in DEPOSITABLE_TOKENS and token_id not in DEPOSITABLE_TOKENS[network_id]:
                return f"Error: Token {token_id} cannot be deposited on {network_id}. Supported tokens: {', '.join(DEPOSITABLE_TOKENS[network_id])}"
        
            # Get chain id
            chain_id = NETWORK_ID_TO_CHAIN_ID.get(network_id)
            if not chain_id:
                return f"Unsupported network: {network_id}"
            
            logger.info(f"Attempting deposit on chain {chain_id} ({network_id}) for token {token_id}")
            
            # Initialize Web3
            if not self._initialize_web3(chain_id):
                return f"Failed to initialize Web3 for network {network_id}. Please check RPC configuration."
            
            # Get token address
            token_address = self._get_token_address(network_id, token_id)
            logger.info(f"Using token address: {token_address} for {token_id}")
            
            # Convert amount to Wei for native tokens, or use token decimals for ERC20
            if token_address == NATIVE_TOKEN_ADDRESS:
                amount_wei = Web3.to_wei(float(params.amount), 'ether')
                # Check user's native token balance
                user_address = wallet_provider.get_address()
                native_balance = wallet_provider.get_balance()
                
                if native_balance < amount_wei:
                    formatted_balance = format_amount_with_decimals(native_balance, 18)
                    return f"Insufficient {token_id.upper()} balance. You have {formatted_balance}, but trying to deposit {params.amount}"
            else:
                # For ERC20 tokens, get decimals and convert amount
                token_contract = self._get_contract(chain_id, token_address, ERC20_ABI)
                try:
                    decimals = token_contract.functions.decimals().call()
                    amount_wei = int(float(params.amount) * (10 ** decimals))
                    
                    # Check user's token balance
                    user_address = wallet_provider.get_address()
                    token_balance = token_contract.functions.balanceOf(user_address).call()
                    
                    if token_balance < amount_wei:
                        formatted_balance = format_amount_with_decimals(token_balance, decimals)
                        return f"Insufficient {token_id.upper()} balance. You have {formatted_balance}, but trying to deposit {params.amount}"
                except Exception as e:
                    logger.error(f"Error getting token details: {str(e)}")
                    return f"Failed to get details for token {token_id}: {str(e)}"
            
            # Send the transaction
            try:
                logger.info(f"Sending deposit transaction for {params.amount} {token_id}")
                tx_hash = self._deposit_to_margin(
                    wallet_provider=wallet_provider,
                    chain_id=chain_id,
                    token_address=token_address,
                    amount=params.amount
                )
                
                logger.info(f"Deposit transaction sent: {tx_hash}")
                
                # Wait for receipt with timeout
                receipt = wallet_provider.wait_for_transaction_receipt(tx_hash, timeout=180)
                
                # Check status
                if receipt['status'] == 1:
                    return f"Successfully deposited {params.amount} {token_id.upper()} to margin account. Transaction hash: {tx_hash}"
                else:
                    logger.error(f"Deposit transaction failed. Hash: {tx_hash}, Receipt: {receipt}")
                    return f"Margin deposit transaction failed. Transaction hash: {tx_hash}"
            except Exception as e:
                logger.error(f"Error in deposit transaction: {str(e)}")
                return f"Error during deposit: {str(e)}"
            
        except Exception as e:
            logger.error(f"Unexpected error in deposit_margin: {str(e)}")
            return f"Unexpected error: {str(e)}"
    
    @create_action(
        name="view-margin-balance",
        description="""
This tool allows viewing the balance of a token in your Kuru margin account.
It takes:
- token_id: The token to check (usdc, usdt, dak, chog, yaki, or native for MON/ETH)
- network_id: (Optional) Network ID (default: monad-testnet)

Example:
- Check MON balance: token_id=native

Important notes:
- This is a read-only action that does not require gas
- On Monad testnet, typically only MON (native) balances will be present after deposits
""",
        schema=MarginActionParams
    )
    def view_margin_balance(self, wallet_provider: EvmWalletProvider, args: Dict[str, Any]) -> str:
        """View token balance in margin account"""
        params = MarginActionParams(**args)
        network_id = params.network_id
        
        # Get chain id
        chain_id = NETWORK_ID_TO_CHAIN_ID.get(network_id)
        if not chain_id:
            return f"Unsupported network: {network_id}"
        
        # Initialize Web3
        if not self._initialize_web3(chain_id):
            return f"Failed to initialize Web3 for network {network_id}"
        
        try:
            # Get token address
            token_address = self._get_token_address(network_id, params.token_id)
            
            # Get balance
            balance = self._get_margin_balance(
                wallet_provider=wallet_provider,
                chain_id=chain_id,
                token_address=token_address
            )
            
            # Convert from wei to decimal
            balance_decimal = Web3.from_wei(balance, 'ether')
            
            return f"Margin account balance for {params.token_id}: {balance_decimal}"
            
        except Exception as e:
            return f"Failed to get margin balance: {str(e)}"
    
    @create_action(
        name="get-orderbook",
        description="""
This tool allows viewing the current orderbook for a market.
It takes:
- market_id: The market to view (mon-usdc, dak-mon, chog-mon, yaki-mon)
- network_id: (Optional) Network ID (default: monad-testnet)

Example:
- View MON/USDC orderbook: market_id=mon-usdc

Important notes:
- This is a read-only action that does not require gas
- Returns the current state of bids and asks
- Supported markets: mon-usdc, dak-mon, chog-mon, yaki-mon
""",
        schema=OrderbookParams
    )
    def get_orderbook(self, wallet_provider: EvmWalletProvider, args: Dict[str, Any]) -> str:
        """Get the current orderbook for a market"""
        params = OrderbookParams(**args)
        network_id = params.network_id
        
        # Get chain id
        chain_id = NETWORK_ID_TO_CHAIN_ID.get(network_id)
        if not chain_id:
            return f"Unsupported network: {network_id}"
        
        # Initialize Web3
        if not self._initialize_web3(chain_id):
            return f"Failed to initialize Web3 for network {network_id}"
        
        try:
            # Get market address
            market_address = self._get_market_address(network_id, params.market_id)
            
            # Get orderbook
            orderbook = self._get_orderbook(
                wallet_provider=wallet_provider,
                chain_id=chain_id,
                market_address=market_address
            )
            
            # Format the output
            bids_output = "\n".join([f"Price: {bid['price']}, Size: {bid['size']}" for bid in orderbook["bids"][:5]])
            asks_output = "\n".join([f"Price: {ask['price']}, Size: {ask['size']}" for ask in orderbook["asks"][:5]])
            
            if not bids_output:
                bids_output = "No bids available"
            if not asks_output:
                asks_output = "No asks available"
                
            return f"Orderbook for {params.market_id}:\n\nTop 5 Bids:\n{bids_output}\n\nTop 5 Asks:\n{asks_output}"
            
        except Exception as e:
            return f"Failed to get orderbook: {str(e)}"
        
    @create_action(
        name="get-portfolio",
        description="""
This tool allows viewing your current portfolio details on Kuru DEX.
It takes:
- network_id: (Optional) Network ID (default: monad-testnet)

Example:
- View your Kuru portfolio: network_id=monad-testnet

Important notes:
- This is a read-only action that does not require gas
- Returns your current balances, open orders, and positions across markets
- Provides a consolidated view of your Kuru activity
""",
        schema=OrderbookParams  # Reusing this schema as it has network_id
    )
    def get_portfolio(self, wallet_provider: EvmWalletProvider, args: Dict[str, Any]) -> str:
        """Get a comprehensive view of user's portfolio on Kuru"""
        params = OrderbookParams(**args)
        network_id = params.network_id
        
        # Get chain id
        chain_id = NETWORK_ID_TO_CHAIN_ID.get(network_id)
        if not chain_id:
            return f"Unsupported network: {network_id}"
        
        # Initialize Web3
        if not self._initialize_web3(chain_id):
            return f"Failed to initialize Web3 for network {network_id}"
        
        try:
            # Get user address
            address = wallet_provider.get_address()
            
            # Start building the portfolio markdown
            portfolio_md = f"# Kuru Portfolio Summary\n\n"
            portfolio_md += f"## Wallet Address\n{address}\n\n"
            
            # Add margin account balances section
            portfolio_md += "## Margin Account Balances\n\n"
            
            # Get margin account
            margin_account = self._get_margin_account(chain_id)
            
            # Check balances for each supported token
            tokens_checked = 0
            for token_id in ["usdc", "usdt", "dak", "chog", "yaki", "native"]:
                try:
                    token_address = self._get_token_address(network_id, token_id)
                    balance = self._get_margin_balance(
                        wallet_provider=wallet_provider,
                        chain_id=chain_id,
                        token_address=token_address
                    )
                    
                    if balance > 0:
                        # Format balance for display
                        balance_decimal = Web3.from_wei(balance, 'ether')
                        portfolio_md += f"- **{token_id.upper()}**: {balance_decimal}\n"
                        tokens_checked += 1
                except Exception as e:
                    logger.warning(f"Error checking balance for {token_id}: {str(e)}")
            
            if tokens_checked == 0:
                portfolio_md += "No tokens found in your margin account.\n\n"
            else:
                portfolio_md += "\n"
            
            # Add open orders section - this would require additional contract calls
            portfolio_md += "## Open Orders\n\n"
            portfolio_md += "This feature is under development. Check back soon!\n\n"
            
            # Add trading history section
            portfolio_md += "## Recent Trading Activity\n\n"
            portfolio_md += "This feature is under development. Check back soon!\n\n"
            
            return portfolio_md
            
        except Exception as e:
            return f"Failed to get portfolio details: {str(e)}"

    @create_action(
        name="test-connection",
        description="Test the connection to the Kuru network",
        schema=OrderbookParams  # Reusing this schema as it has network_id
    )
    def test_connection(self, wallet_provider: EvmWalletProvider, args: Dict[str, Any]) -> str:
        """Test connection to the Kuru network"""
        params = OrderbookParams(**args)
        network_id = params.network_id
        
        # Get chain id
        chain_id = NETWORK_ID_TO_CHAIN_ID.get(network_id)
        if not chain_id:
            return f"Unsupported network: {network_id}"
        
        # Try to initialize Web3
        if not self._initialize_web3(chain_id):
            return f"Failed to initialize Web3 for network {network_id}. Please check your RPC configuration."
        
        # Try to get the block number
        try:
            web3 = self.web3_providers[chain_id]
            block_number = web3.eth.block_number
            return f"Successfully connected to {network_id} (chain ID: {chain_id}). Current block number: {block_number}"
        except Exception as e:
            return f"Connected to RPC but failed to get block number: {str(e)}"

def kuru_action_provider(
    rpc_url_by_chain_id: Optional[Dict[int, str]] = None,
    ws_url: Optional[str] = None,
    margin_account_by_chain: Optional[Dict[int, str]] = None,
    kuru_router_addresses: Optional[Dict[int, str]] = None
) -> KuruActionProvider:
    """Create a Kuru action provider
    
    Args:
        rpc_url_by_chain_id: Optional mapping of chain IDs to RPC URLs
        ws_url: Optional WebSocket URL for real-time order updates
        margin_account_by_chain: Optional mapping of chain IDs to margin account addresses
        kuru_router_addresses: Optional mapping of chain IDs to Kuru router addresses
        
    Returns:
        A configured KuruActionProvider instance
    """
    return KuruActionProvider(
        rpc_url_by_chain_id=rpc_url_by_chain_id,
        ws_url=ws_url,
        margin_account_by_chain=margin_account_by_chain,
        kuru_router_addresses=kuru_router_addresses
    )


















