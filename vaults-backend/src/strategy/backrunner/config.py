import dotenv
from pathlib import Path

CONFIG = dotenv.dotenv_values("mainnet_full.env")

# # Load configuration data from your .env file
# CONFIG = dotenv.dotenv_values("mainnet_archive.env")

# # Use the remote RPC endpoints directly
# NODE_HTTP_URI = CONFIG["NODE_HOST_HTTP"]
# NODE_WEBSOCKET_URI = CONFIG["NODE_HOST_WEBSOCKET"]

# # For IPC, typically local nodes use this, so it can remain if needed.
# NODE_IPC_PATH = CONFIG.get("NODE_IPC_PATH")

# File paths
DATA_DIR = Path(".")
BLACKLIST_FILES = {
    "pools": DATA_DIR / "ethereum_blacklisted_pools.json",
    "tokens": DATA_DIR / "ethereum_blacklisted_tokens.json",
    "arbs": DATA_DIR / "ethereum_blacklisted_arbs.json"
}

# Existing constants
OPERATOR_ADDRESS = CONFIG["OPERATOR_ADDRESS"]
EXECUTOR_CONTRACT_ADDRESS = CONFIG["EXECUTOR_CONTRACT_ADDRESS"]
#NODE_HTTP_URI = CONFIG["NODE_HOST_HTTP"] + ":" + CONFIG["NODE_PORT_HTTP"]
#NODE_WEBSOCKET_URI = CONFIG["NODE_HOST_WEBSOCKET"] + ":" + CONFIG["NODE_PORT_WEBSOCKET"]
NODE_HOST_HTTP = 'https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID'
NODE_HOST_WEBSOCKET = 'wss://mainnet.infura.io/ws/v3/YOUR_INFURA_PROJECT_ID'
NODE_IPC_PATH = CONFIG["NODE_IPC_PATH"]
WETH_ADDRESS = CONFIG["WRAPPED_TOKEN_ADDRESS"]

# Simulation constants
SIMULATION_TIMEOUT = 0.25  # seconds
PRE_CHECK_ENABLED = True

# Add GAS_FEE_MULTIPLIER and any other constants if they exist
GAS_FEE_MULTIPLIER = float(CONFIG.get("GAS_FEE_MULTIPLIER", 1.2))
DRY_RUN = CONFIG.get("DRY_RUN", "True") == "True" 