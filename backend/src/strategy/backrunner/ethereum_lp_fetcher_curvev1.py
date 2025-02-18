import sys
import ujson
import web3
import dotenv
from degenbot.constants import ZERO_ADDRESS
from degenbot.curve.abi import CURVE_V1_FACTORY_ABI, CURVE_V1_REGISTRY_ABI

# Load configuration from file
CONFIG = dotenv.dotenv_values("mainnet_archive.env")
NODE_IPC_PATH = CONFIG["NODE_IPC_PATH"]
BLOCK_SPAN = 5000

def connect_web3():
    w3 = web3.Web3(web3.IPCProvider(NODE_IPC_PATH))
    if not w3.isConnected():
        sys.exit("Could not connect!")
    return w3

def load_lp_data(filename: str):
    try:
        with open(filename) as file:
            return ujson.load(file)
    except FileNotFoundError:
        return []

def save_lp_data(filename: str, data):
    with open(filename, "w") as file:
        ujson.dump(data, file, indent=2)

def fetch_registry_lp_data(w3, registry: dict):
    print(registry["name"])
    contract = w3.eth.contract(address=registry["factory_address"], abi=registry["abi"])
    filename = registry["filename"]
    lp_data = load_lp_data(filename)
    previous_pool_count = len(lp_data)

    current_pool_count = contract.functions.pool_count().call()
    for pool_id in range(previous_pool_count, current_pool_count):
        pool_address = contract.functions.pool_list(pool_id).call()
        pool_coin_addresses = contract.functions.get_coins(pool_address).call()
        pool_is_meta = contract.functions.is_meta(pool_address).call()
        pool_entry = {
            "pool_address": pool_address,
            "pool_id": pool_id,
            "type": registry["pool_type"],
            "coin_addresses": [coin for coin in pool_coin_addresses if coin != ZERO_ADDRESS],
        }
        if pool_is_meta:
            underlying = contract.functions.get_underlying_coins(pool_address).call()
            pool_entry["underlying_coin_addresses"] = [coin for coin in underlying if coin != ZERO_ADDRESS]
        lp_data.append(pool_entry)
    save_lp_data(filename, lp_data)
    print(f"Saved {len(lp_data)} pools ({len(lp_data) - previous_pool_count} new)")

def main():
    w3 = connect_web3()
    registries = [
        {
            "name": "Curve V1: Base Registry",
            "filename": "ethereum_lps_curvev1_registry.json",
            "factory_address": "0x90E00ACe148ca3b23Ac1bC8C240C2a7Dd9c2d7f5",
            "pool_type": "CurveV1",
            "abi": CURVE_V1_REGISTRY_ABI,
        },
        {
            "name": "Curve V1: Factory",
            "filename": "ethereum_lps_curvev1_factory.json",
            "factory_address": "0x127db66E7F0b16470Bec194d0f496F9Fa065d0A9",
            "pool_type": "CurveV1",
            "abi": CURVE_V1_FACTORY_ABI,
        },
    ]
    for registry in registries:
        fetch_registry_lp_data(w3, registry)

if __name__ == "__main__":
    main()