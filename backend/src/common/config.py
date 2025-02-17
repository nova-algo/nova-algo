import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ETHEREUM_RPC_URL = os.getenv("ETHEREUM_RPC_URL")
    ETHEREUM_PRIVATE_KEY = os.getenv("ETHEREUM_PRIVATE_KEY")
    UNISWAP_ROUTER_ADDRESS = os.getenv("UNISWAP_ROUTER_ADDRESS")
    
    MIN_PROFIT_GROSS = int(0.0005 * 10**18)
    MIN_PROFIT_NET = int(0.000005 * 10**18)
    BRIBE = 0.95
    BRIBE_BIPS = int(10_000 * BRIBE) 