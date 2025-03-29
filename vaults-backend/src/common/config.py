from typing import Dict, Any
import os
from dotenv import load_dotenv
from eth_utils import to_checksum_address
from web3 import Web3
from decimal import Decimal

# Load environment variables
load_dotenv()

class UniswapConfig:
    # Node connection
    NODE_HTTP_URI = f"{os.getenv('NODE_HOST_HTTP')}:{os.getenv('NODE_PORT_HTTP')}"
    NODE_WEBSOCKET_URI = f"{os.getenv('NODE_HOST_WEBSOCKET')}:{os.getenv('NODE_PORT_WEBSOCKET')}"
    NODE_IPC_PATH = os.getenv('NODE_IPC_PATH')
    
    # Contract addresses
    WETH_ADDRESS = to_checksum_address(os.getenv('WRAPPED_TOKEN_ADDRESS'))
    EXECUTOR_ADDRESS = to_checksum_address(os.getenv('EXECUTOR_CONTRACT_ADDRESS'))
    
    # Transaction parameters
    MIN_PROFIT_GROSS = int(0.0005 * 10**18)  # 0.0005 ETH
    MIN_PROFIT_NET = int(0.000005 * 10**18)  # 0.000005 ETH
    BRIBE_PERCENTAGE = 0.95  # 95% of profit
    BRIBE_BIPS = int(10_000 * BRIBE_PERCENTAGE)
    
    # Monitoring settings
    SUBSCRIBE_TO_FULL_TRANSACTIONS = True
    EVENT_PROCESS_DELAY = 0.1
    AVERAGE_BLOCK_TIME = 12.0
    
    # Builder endpoints
    BUILDERS = [
        "https://rpc.titanbuilder.xyz",
        "https://builder0x69.io",
        "https://rpc.beaverbuild.org",
        "https://rsync-builder.xyz",
        "https://relay.flashbots.net",
    ]

    @staticmethod
    def load_abi(filename: str) -> str:
        """Load ABI from file"""
        with open(f"src/common/abis/{filename}.json") as f:
            return f.read()

    # Load contract ABIs
    EXECUTOR_ABI = os.getenv('EXECUTOR_CONTRACT_ABI')

class Config:
    ETHEREUM_RPC_URL = os.getenv("ETHEREUM_RPC_URL")
    ETHEREUM_PRIVATE_KEY = os.getenv("ETHEREUM_PRIVATE_KEY")
    UNISWAP_ROUTER_ADDRESS = os.getenv("UNISWAP_ROUTER_ADDRESS")
    
    MIN_PROFIT_GROSS = int(0.0005 * 10**18)
    MIN_PROFIT_NET = int(0.000005 * 10**18)
    BRIBE = 0.95
    BRIBE_BIPS = int(10_000 * BRIBE) 

# 1. Pool State Management
class PoolStateManager:
    def __init__(self):
        self.pools = {}
        self.snapshot = UniswapV3LiquiditySnapshot()

# 2. Transaction Monitoring
class TransactionMonitor:
    def __init__(self, w3, config):
        self.w3 = w3
        self.pending_tx = {}
        self.backrun_hashes = set()

# 3. Arbitrage Execution
class ArbitrageExecutor:
    def __init__(self, w3, config):
        self.w3 = w3
        self.executor_contract = None
        self.min_profit = Decimal('0.001')