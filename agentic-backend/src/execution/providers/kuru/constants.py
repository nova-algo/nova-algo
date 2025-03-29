"""Constants for Kuru action provider."""
import json
import os
from pathlib import Path
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Define the path to the ABI files
ABIS_DIR = os.path.join(os.path.dirname(__file__), "abis")

# Load ABI from JSON file
def load_abi(file_name):
    """Load ABI from file"""
    try:
        with open(os.path.join(ABIS_DIR, file_name), 'r') as f:
            abi_json = json.load(f)
            # Extract just the ABI array from the JSON file
            return abi_json['abi'] if 'abi' in abi_json else abi_json
    except Exception as e:
        logger.error(f"Error loading ABI file {file_name}: {str(e)}")
        return []

# Supported networks
SUPPORTED_NETWORKS = ["monad-testnet", "base-sepolia", "base-mainnet"]

# Network ID to Chain ID mapping
NETWORK_ID_TO_CHAIN_ID = {
    "base-mainnet": 8453,
    "base-sepolia": 84532,
    "monad-testnet": 10143
}

# User-friendly market identifiers
MARKET_IDS = {
    "mon-usdc": "MON_USDC",
    "dak-mon": "DAK_MON",
    "chog-mon": "CHOG-MON",
    "yaki-mon": "YAKI-MON"
}

# Market addresses by network
MARKET_ADDRESSES = {
    "monad-testnet": {
        "mon-usdc": "0xd3af145f1aa1a471b5f0f62c52cf8fcdc9ab55d3",
        "dak-mon": "0x94b72620e65577de5fb2b8a8b93328caf6ca161b",
        "chog-mon": "0x277bf4a0aac16f19d7bf592feffc8d2d9a890508",
        "yaki-mon": "0xd5c1dc181c359f0199c83045a85cd2556b325de0"
    }
}

# User-friendly token identifiers
SUPPORTED_TOKENS = ["usdc", "usdt", "dak", "chog", "yaki"]

# Contract addresses for tokens by network
TOKEN_ADDRESSES = {
    "monad-testnet": {
        "usdc": "0xf817257fed379853cDe0fa4F97AB987181B1E5Ea", 
        "usdt": "0x88b8E2161DEDC77EF4ab7585569D2415a1C1055D",
        "dak": "0x0F0BDEbF0F83cD1EE3974779Bcb7315f9808c714",
        "chog": "0xE0590015A873bF326bd645c3E1266d4db41C4E6B",
        "yaki": "0xfe140e1dCe99Be9F4F15d657CD9b7BF622270C50"
    }
}

# Native token address (ETH, MON)
NATIVE_TOKEN_ADDRESS = "0x0000000000000000000000000000000000000000"

# Contract addresses by chain_id
KURU_CONTRACT_ADDRESSES = {
    10143: {  # Monad testnet
        "ROUTER": "0xc816865f172d640d93712C68a7E1F83F3fA63235",
        "MARGIN_ACCOUNT": "0x4B186949F31FCA0aD08497Df9169a6bEbF0e26ef",
        "KURU_FORWARDER": "0x350678D87BAa7f513B262B7273ad8Ccec6FF0f78",
        "KURU_DEPLOYER": "0x67a4e43C7Ce69e24d495A39c43489BC7070f009B",
        "KURU_UTILS": "0x9E50D9202bEc0D046a75048Be8d51bBa93386Ade"
    }
}

# Default RPC URLs for each chain
DEFAULT_RPC_URLS = {
    8453: "https://base-mainnet.public.blastapi.io",  # Base Mainnet
    84532: "https://sepolia.base.org",  # Base Sepolia
    10143: "https://testnet-rpc.monad.xyz",  # Monad Testnet
}

# Load ABIs
MARGIN_ACCOUNT_ABI = load_abi('kuru_margin.json')
KURU_MARKET_ABI = load_abi('order_book.json')
KURU_FORWARDER_ABI = load_abi('kuru_forwarder.json')
IERC20_ABI = load_abi('ierc20.json')
KURU_ROUTER_ABI = load_abi('kuru_router.json')
KURU_MARGIN_ABI = load_abi('kuru_margin.json')

# Aliases for compatibility
ERC20_ABI = IERC20_ABI

# Kuru Market ABI (simplified example - this would need to be filled with actual ABI)
# KURU_MARKET_ABI = [
#     {
#         "inputs": [
#             {"internalType": "uint8", "name": "side", "type": "uint8"},
#             {"internalType": "uint256", "name": "price", "type": "uint256"},
#             {"internalType": "uint256", "name": "size", "type": "uint256"},
#             {"internalType": "uint8", "name": "orderType", "type": "uint8"},
#             {"internalType": "uint8", "name": "postOnly", "type": "uint8"},
#             {"internalType": "uint256", "name": "minAmountOut", "type": "uint256"},
#             {"internalType": "string", "name": "cloid", "type": "string"}
#         ],
#         "name": "createOrder",
#         "outputs": [],
#         "stateMutability": "nonpayable",
#         "type": "function"
#     },
#     {
#         "inputs": [
#             {"internalType": "string", "name": "cloid", "type": "string"}
#         ],
#         "name": "cancelOrder",
#         "outputs": [],
#         "stateMutability": "nonpayable",
#         "type": "function"
#     },
#     {
#         "inputs": [
#             {"internalType": "uint8[]", "name": "sides", "type": "uint8[]"},
#             {"internalType": "uint256[]", "name": "prices", "type": "uint256[]"},
#             {"internalType": "uint256[]", "name": "sizes", "type": "uint256[]"},
#             {"internalType": "uint8[]", "name": "orderTypes", "type": "uint8[]"},
#             {"internalType": "uint8[]", "name": "postOnlys", "type": "uint8[]"},
#             {"internalType": "uint256[]", "name": "minAmountsOut", "type": "uint256[]"},
#             {"internalType": "string[]", "name": "cloids", "type": "string[]"}
#         ],
#         "name": "batchOrders",
#         "outputs": [],
#         "stateMutability": "nonpayable",
#         "type": "function"
#             # ... continued from previous response ...
#     },
#     {
#         "inputs": [],
#         "name": "getBids",
#         "outputs": [
#             {
#                 "components": [
#                     {"internalType": "uint256", "name": "price", "type": "uint256"},
#                     {"internalType": "uint256", "name": "size", "type": "uint256"},
#                     {"internalType": "string", "name": "orderId", "type": "string"}
#                 ],
#                 "internalType": "struct OrderInfo[]",
#                 "name": "",
#                 "type": "tuple[]"
#             }
#         ],
#         "stateMutability": "view",
#         "type": "function"
#     },
#     {
#         "inputs": [],
#         "name": "getAsks",
#         "outputs": [
#             {
#                 "components": [
#                     {"internalType": "uint256", "name": "price", "type": "uint256"},
#                     {"internalType": "uint256", "name": "size", "type": "uint256"},
#                     {"internalType": "string", "name": "orderId", "type": "string"}
#                 ],
#                 "internalType": "struct OrderInfo[]",
#                 "name": "",
#                 "type": "tuple[]"
#             }
#         ],
#         "stateMutability": "view",
#         "type": "function"
#     },
#     {
#         "inputs": [
#             {"internalType": "string", "name": "orderId", "type": "string"}
#         ],
#         "name": "getOrderStatus",
#         "outputs": [
#             {
#                 "components": [
#                     {"internalType": "uint8", "name": "status", "type": "uint8"},
#                     {"internalType": "uint256", "name": "filledSize", "type": "uint256"},
#                     {"internalType": "uint256", "name": "remainingSize", "type": "uint256"},
#                     {"internalType": "uint256", "name": "price", "type": "uint256"}
#                 ],
#                 "internalType": "struct OrderStatus",
#                 "name": "",
#                 "type": "tuple"
#             }
#         ],
#         "stateMutability": "view",
#         "type": "function"
#     }
# ]

# Kuru Router ABI (simplified example)
# KURU_ROUTER_ABI = [
#     {
#         "inputs": [
#             {"internalType": "address", "name": "tokenIn", "type": "address"},
#             {"internalType": "address", "name": "tokenOut", "type": "address"},
#             {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
#             {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"}
#         ],
#         "name": "swapExactTokensForTokens",
#         "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
#         "stateMutability": "nonpayable",
#         "type": "function"
#     }
# ]

# Kuru Margin Account ABI (simplified example)
# KURU_MARGIN_ABI = [
#     {
#         "inputs": [
#             {"internalType": "address", "name": "token", "type": "address"},
#             {"internalType": "uint256", "name": "amount", "type": "uint256"}
#         ],
#         "name": "deposit",
#         "outputs": [],
#         "stateMutability": "nonpayable",
#         "type": "function"
#     },
#     {
#         "inputs": [
#             {"internalType": "address", "name": "token", "type": "address"},
#             {"internalType": "uint264", "name": "amount", "type": "uint256"}
#         ],
#         "name": "withdraw",
#         "outputs": [],
#         "stateMutability": "nonpayable",
#         "type": "function"
#     },
#     {
#         "inputs": [
#             {"internalType": "address", "name": "", "type": "address"}
#         ],
#         "name": "tokenBalances",
#         "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
#         "stateMutability": "view",
#         "type": "function"
#     }
# ]

# # ERC20 token ABI (for approvals)
ERC20_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "spender", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "account", "type": "address"}
        ],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "owner", "type": "address"},
            {"internalType": "address", "name": "spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# Tokens that can be deposited by network
DEPOSITABLE_TOKENS = {
    "monad-testnet": ["native"],  # Only MON can be deposited on Monad testnet
    "base-sepolia": ["native", "usdc", "usdt"],  # Example for Base Sepolia
    "base-mainnet": ["native", "usdc", "usdt"]  # Example for Base Mainnet
}