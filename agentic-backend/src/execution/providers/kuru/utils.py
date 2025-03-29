"""Utility functions for Kuru action provider."""

from typing import Any, Dict, Optional, Union, List, Tuple
from decimal import Decimal

import logging
from web3 import Web3
from web3.types import Wei

from coinbase_agentkit.wallet_providers import EvmWalletProvider
from .constants import ERC20_ABI, TOKEN_ADDRESSES, MARKET_ADDRESSES, NETWORK_ID_TO_CHAIN_ID

# Set up logging
logger = logging.getLogger(__name__)

def get_token_address(network_id: str, token_id: str) -> str:
    """Get token address from token ID for a specific network
    
    Args:
        network_id: Network ID (e.g., "monad-testnet")
        token_id: Token ID (e.g., "usdc", "native")
        
    Returns:
        Token address
        
    Raises:
        ValueError: If token not found
    """
    # Native token has a special address
    if token_id.lower() == "native":
        return "0x0000000000000000000000000000000000000000"
    
    try:
        return TOKEN_ADDRESSES[network_id][token_id.lower()]
    except KeyError:
        raise ValueError(f"Unknown token: {token_id} for network {network_id}")

def get_market_address(network_id: str, market_id: str) -> str:
    """Get market address from market ID for a specific network
    
    Args:
        network_id: Network ID (e.g., "monad-testnet")
        market_id: Market ID (e.g., "mon-usdc")
        
    Returns:
        Market address
        
    Raises:
        ValueError: If market not found
    """
    try:
        return MARKET_ADDRESSES[network_id][market_id.lower()]
    except KeyError:
        raise ValueError(f"Unknown market: {market_id} for network {network_id}")

def format_amount_with_decimals(amount: Union[str, int, float, Decimal], decimals: int = 18) -> int:
    """Format human-readable amount to wei
    
    Args:
        amount: Amount in human-readable format (e.g., "1.5")
        decimals: Token decimals
        
    Returns:
        Amount in wei
    """
    if isinstance(amount, str):
        amount = Decimal(amount)
    
    if isinstance(amount, (int, float)):
        amount = Decimal(str(amount))
    
    # Convert to wei
    return int(amount * Decimal(10) ** Decimal(decimals))

def format_amount_from_decimals(amount: int, decimals: int = 18) -> str:
    """Format wei amount to human-readable format
    
    Args:
        amount: Amount in wei
        decimals: Token decimals
        
    Returns:
        Human-readable amount
    """
    # Convert from wei
    return str(Decimal(amount) / Decimal(10) ** Decimal(decimals))

def get_token_symbol(wallet_provider: EvmWalletProvider, token_address: str) -> str:
    """Get token symbol
    
    Args:
        wallet_provider: Wallet provider
        token_address: Token address
        
    Returns:
        Token symbol
    """
    # Native token
    if token_address == "0x0000000000000000000000000000000000000000":
        network = wallet_provider.get_network()
        # Return appropriate symbol based on network
        if network.network_id.startswith("monad"):
            return "MON"
        return "ETH"
    
    try:
        # Create contract instance
        contract = wallet_provider._web3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=ERC20_ABI
        )
        
        # Call symbol function
        return contract.functions.symbol().call()
    except Exception as e:
        logger.warning(f"Error getting token symbol: {str(e)}")
        return "UNKNOWN"

def get_portfolio_summary(wallet_provider: EvmWalletProvider, market_address: str) -> str:
    """Get portfolio summary in markdown format
    
    Args:
        wallet_provider: Wallet provider
        market_address: Market address
        
    Returns:
        Markdown-formatted portfolio summary
    """
    # This would be a more complex implementation for Kuru
    # Similar to Compound's get_portfolio_details_markdown
    
    address = wallet_provider.get_address()
    
    # This is a simplified version - you would need to expand this
    # based on Kuru's specific contract interactions
    
    return f"""
## Kuru Portfolio Summary

### Wallet Address
{address}

### Balances
*Currently not available for this market*

### Open Orders
*Currently not available for this market*

"""

def get_token_decimals(wallet_provider: EvmWalletProvider, token_address: str) -> int:
    """Get token decimals"""
    # ETH has 18 decimals
    if token_address == "0x0000000000000000000000000000000000000000":
        return 18
    
    # For ERC20 tokens, get decimals from contract
    try:
        # Create contract instance
        contract = wallet_provider._web3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=ERC20_ABI
        )
        
        # Call decimals function
        return contract.functions.decimals().call()
    except Exception as e:
        # Default to 18 decimals if something goes wrong
        return 18

def get_token_balance(wallet_provider: EvmWalletProvider, token_address: str) -> int:
    """Get token balance for address"""
    address = wallet_provider.get_address()
    
    # For ETH, get balance from web3
    if token_address == "0x0000000000000000000000000000000000000000":
        #wallet_provider.get_balance(address)
        return wallet_provider._web3.eth.get_balance(address)
    
    # For ERC20 tokens, call balanceOf
    try:
        # Create contract instance
        contract = wallet_provider._web3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=ERC20_ABI
        )
        
        # Call balanceOf function
        return contract.functions.balanceOf(address).call()
    except Exception as e:
        return 0

def approve_token(wallet_provider: EvmWalletProvider, token_address: str, spender_address: str, amount: int) -> Dict[str, Any]:
    """Approve a spender to use tokens
    
    Args:
        wallet_provider: The wallet provider
        token_address: The address of the token to approve
        spender_address: The address of the spender to approve
        amount: The amount to approve in wei
        
    Returns:
        Transaction receipt
        
    Raises:
        Exception: If the approval transaction fails
    """
    # Native ETH doesn't need approval
    if token_address == "0x0000000000000000000000000000000000000000":
        return None
        
    try:
        # Create token contract
        contract = Web3().eth.contract(address=token_address, abi=ERC20_ABI)
        
        # Encode the approve function call
        encoded_data = contract.encodeABI(
            fn_name="approve",
            args=[spender_address, amount]
        )
        
        # Prepare transaction
        tx_params = {
            "to": token_address,
            "data": encoded_data,
        }
        
        # Send transaction
        tx_hash = wallet_provider.send_transaction(tx_params)
        
        # Wait for receipt and return it
        receipt = wallet_provider.wait_for_transaction_receipt(tx_hash)
        
        if receipt["status"] != 1:
            raise Exception(f"Approval transaction failed with hash: {tx_hash}")
            
        return receipt
    except Exception as e:
        raise Exception(f"Error approving token: {str(e)}")

def estimate_gas_with_buffer(
    tx_params: Dict[str, Any],
    buffer_percentage: float = 20.0
) -> int:
    """Estimate gas with buffer"""
    try:
        gas_estimate = Web3().eth.estimate_gas(tx_params)
        # Add buffer for safety
        return int(gas_estimate * (1 + buffer_percentage / 100))
    except Exception as e:
        # Fallback to default gas limit
        logger.warning(f"Error estimating gas: {str(e)}")
        return 500000  # Default gas limit

# Additional market helper functions

def get_market_tokens(network_id: str, market_id: str) -> Tuple[str, str]:
    """Get base and quote token IDs for a market
    
    Args:
        network_id: Network ID
        market_id: Market ID
        
    Returns:
        Tuple of (base_token_id, quote_token_id)
    """
    # Parse market ID to get tokens
    # For example, "mon-usdc" would return ("native", "usdc")
    parts = market_id.lower().split("-")
    
    if len(parts) == 2:
        # Standard format like "mon-usdc"
        if parts[0] == "mon":
            base_token = "native"
        else:
            base_token = parts[0]
            
        quote_token = parts[1]
        return (base_token, quote_token)
    else:
        # Handle formats like "chog-mon"
        if parts[1] == "mon":
            quote_token = "native"
        else:
            quote_token = parts[1]
            
        base_token = parts[0]
        return (base_token, quote_token)

def get_token_name(wallet_provider: EvmWalletProvider, token_address: str) -> str:
    """Get token name
    
    Args:
        wallet_provider: Wallet provider
        token_address: Token address
        
    Returns:
        Token name
    """
    # Native token
    if token_address == "0x0000000000000000000000000000000000000000":
        network = wallet_provider.get_network()
        # Return appropriate name based on network
        if network.network_id.startswith("monad"):
            return "Monad"
        return "Ethereum"
    
    try:
        # Create contract instance
        contract = wallet_provider._web3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=ERC20_ABI
        )
        
        # Call name function
        return contract.functions.name().call()
    except Exception as e:
        logger.warning(f"Error getting token name: {str(e)}")
        return "Unknown Token"

# from typing import Optional, Dict, Any
# from decimal import Decimal
# import asyncio
# from web3 import Web3

# from .constants import TOKEN_ADDRESSES

# def get_token_address(chain_id: int, symbol: str) -> Optional[str]:
#     """Get the token address for a given symbol and chain ID"""
#     chain_tokens = TOKEN_ADDRESSES.get(chain_id, {})
#     return chain_tokens.get(symbol.upper())

# def format_token_amount(amount: Decimal, decimals: int = 18) -> str:
#     """Format a token amount with the correct number of decimals"""
#     return str(int(amount * Decimal(10) ** decimals))

# async def approve_token(client, wallet_provider, token_address: str, spender_address: str, amount: float) -> str:
#     """Approve spender to use tokens
    
#     Args:
#         client: KuruClient instance
#         wallet_provider: Wallet provider
#         token_address: Address of token to approve
#         spender_address: Address of spender to approve
#         amount: Amount to approve (in decimal units)
    
#     Returns:
#         Transaction hash of the approval transaction
#     """
#     # Convert amount to appropriate units
#     token_info = await client.get_token_info(token_address)
#     decimals = token_info.get('decimals', 18)
#     amount_wei = Web3.to_wei(amount, 'ether' if decimals == 18 else 'mwei' if decimals == 6 else 'ether')
    
#     # Prepare the approval transaction
#     approval_data = client.token_contract.encodeABI(
#         fn_name='approve',
#         args=[spender_address, amount_wei]
#     )
    
#     params = {
#         'to': token_address,
#         'data': approval_data
#     }
    
#     # Send the transaction
#     tx_hash = wallet_provider.send_transaction(params)
    
#     # Wait for the transaction to be mined
#     await client.wait_for_transaction(tx_hash)
    
#     return tx_hash

# async def verify_transaction_success(client, tx_hash: str, max_attempts: int = 5) -> bool:
#     """Verify that a transaction was successful"""
#     for i in range(max_attempts):
#         try:
#             receipt = await client.wait_for_transaction(tx_hash)
#             if receipt and receipt.get('status') == 1:
#                 return True
#             elif receipt:
#                 return False
#         except Exception:
#             if i == max_attempts - 1:
#                 return False
#             # Wait longer between attempts
#             await asyncio.sleep(2 ** i)  # Exponential backoff
#     return False