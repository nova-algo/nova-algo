import ujson
import time
import itertools
import networkx as nx
import web3

# Constant definition
WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
BLACKLISTED_TOKENS = [
    # "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
    # "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
]

def load_lp_data(filenames: list, exclude_keys=None):
    """Load LP data from a list of filenames."""
    data = {}
    exclude_keys = exclude_keys or []
    for filename in filenames:
        try:
            with open(filename) as file:
                pools = ujson.load(file)
            for pool in pools:
                key = pool.get("pool_address")
                # Exclude keys like "pool_id"
                data[key] = {k: v for k, v in pool.items() if k not in exclude_keys}
        except FileNotFoundError:
            print(f"File {filename} not found.")
    return data

def build_liquidity_graph(v2_lp_data, v3_lp_data, curve_v1_lp_data):
    """Build a graph with tokens as nodes and pools as edges."""
    G = nx.MultiGraph()
    # Build graph for Uniswap V2 pools.
    for pool in v2_lp_data.values():
        G.add_edge(pool["token0"], pool["token1"],
                   lp_address=pool["pool_address"],
                   pool_type="UniswapV2")
    # Build graph for Uniswap V3 pools.
    for pool in v3_lp_data.values():
        G.add_edge(pool["token0"], pool["token1"],
                   lp_address=pool["pool_address"],
                   pool_type="UniswapV3")
    # For Curve V1, add edges for underlying tokens and coin addresses.
    for pool in curve_v1_lp_data.values():
        if pool.get("underlying_coin_addresses"):
            for token_pair in itertools.combinations(pool["underlying_coin_addresses"], 2):
                G.add_edge(*token_pair,
                           lp_address=pool["pool_address"],
                           pool_type="CurveV1")
        for token_pair in itertools.combinations(pool["coin_addresses"], 2):
            G.add_edge(*token_pair,
                       lp_address=pool["pool_address"],
                       pool_type="CurveV1")
    G.remove_nodes_from(BLACKLISTED_TOKENS)
    return G

def find_triangular_paths(G, v2_lp_data, v3_lp_data, curve_v1_lp_data):
    """Find triangular arbitrage paths involving WETH."""
    triangle_arb_paths = {}
    tokens_with_weth = list(G.neighbors(WETH_ADDRESS))
    # Consider only tokens with more than one connection.
    filtered_tokens = [t for t in tokens_with_weth if G.degree(t) > 1]
    
    for token_a, token_b in itertools.combinations(filtered_tokens, 2):
        # Ensure direct connection exists
        if not G.get_edge_data(token_a, token_b):
            continue
        # Get CurveV1 pools for tokenA/tokenB pair.
        inside_pools = [
            edge["lp_address"]
            for edge in G.get_edge_data(token_a, token_b).values()
            if edge["pool_type"] == "CurveV1"
        ]
        # Remove metapools that are not beneficial.
        for pool in inside_pools.copy():
            pool_data = curve_v1_lp_data[pool]
            if pool_data.get("underlying_coin_addresses") and all(
                token in pool_data["underlying_coin_addresses"] for token in [token_a, token_b]
            ):
                inside_pools.remove(pool)
        if not inside_pools:
            continue
        
        # Get outside pools (only Uniswap here) connecting with WETH.
        outside_pools_tokenA = [
            edge["lp_address"]
            for edge in G.get_edge_data(token_a, WETH_ADDRESS).values()
            if edge["pool_type"] in ["UniswapV2", "UniswapV3"]
        ]
        outside_pools_tokenB = [
            edge["lp_address"]
            for edge in G.get_edge_data(token_b, WETH_ADDRESS).values()
            if edge["pool_type"] in ["UniswapV2", "UniswapV3"]
        ]
        # Build two types of triangle routes:
        for pool_addresses in itertools.product(outside_pools_tokenA, inside_pools, outside_pools_tokenB):
            path_id = web3.Web3.keccak(
                hexstr="".join([addr[2:] for addr in pool_addresses])
            ).hex()
            pool_info = {}
            for pool_address in pool_addresses:
                if pool_address in v2_lp_data:
                    pool_info[pool_address] = v2_lp_data[pool_address]
                elif pool_address in v3_lp_data:
                    pool_info[pool_address] = v3_lp_data[pool_address]
                elif pool_address in curve_v1_lp_data:
                    pool_info[pool_address] = curve_v1_lp_data[pool_address]
                else:
                    raise Exception("Pool not found")
            triangle_arb_paths[path_id] = {
                "id": path_id,
                "path": pool_addresses,
                "pools": pool_info,
            }
        for pool_addresses in itertools.product(outside_pools_tokenB, inside_pools, outside_pools_tokenA):
            path_id = web3.Web3.keccak(
                hexstr="".join([addr[2:] for addr in pool_addresses])
            ).hex()
            pool_info = {}
            for pool_address in pool_addresses:
                if pool_address in v2_lp_data:
                    pool_info[pool_address] = v2_lp_data[pool_address]
                elif pool_address in v3_lp_data:
                    pool_info[pool_address] = v3_lp_data[pool_address]
                elif pool_address in curve_v1_lp_data:
                    pool_info[pool_address] = curve_v1_lp_data[pool_address]
                else:
                    raise Exception("Pool not found")
            triangle_arb_paths[path_id] = {
                "id": path_id,
                "path": pool_addresses,
                "pools": pool_info,
            }
    return triangle_arb_paths

def main():
    start_timer = time.perf_counter()

    v2_lp_data = load_lp_data([
        "ethereum_lps_sushiswapv2.json", "ethereum_lps_uniswapv2.json"
    ], exclude_keys=["pool_id"])
    print(f"Found {len(v2_lp_data)} V2 pools")

    v3_lp_data = load_lp_data([
        "ethereum_lps_sushiswapv3.json", "ethereum_lps_uniswapv3.json"
    ])
    # Remove the metadata entry if present.
    if v3_lp_data:
        list(v3_lp_data.popitem())
    print(f"Found {len(v3_lp_data)} V3 pools")

    curve_v1_lp_data = load_lp_data([
        "ethereum_lps_curvev1_factory.json", "ethereum_lps_curvev1_registry.json"
    ])
    print(f"Found {len(curve_v1_lp_data)} Curve V1 pools")

    # Build liquidity graph.
    G = build_liquidity_graph(v2_lp_data, v3_lp_data, curve_v1_lp_data)
    print(f"G ready: {len(G.nodes)} nodes, {len(G.edges)} edges")

    # Find arbitrage paths
    triangle_paths = find_triangular_paths(G, v2_lp_data, v3_lp_data, curve_v1_lp_data)
    print(f"Found {len(triangle_paths)} triangle arb paths in {time.perf_counter() - start_timer:.1f}s")

    # Save results
    with open("ethereum_arbs_3pool_curve.json", "w") as file:
        ujson.dump(triangle_paths, file, indent=2)
    print("Arb paths saved to ethereum_arbs_3pool_curve.json")

if __name__ == "__main__":
    main()