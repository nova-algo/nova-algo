"""Kuru action provider package."""

from .kuru_action_provider import kuru_action_provider, KuruActionProvider

__all__ = ["kuru_action_provider", "KuruActionProvider"]


# from typing import Dict, Optional
# from .kuru_action_provider import KuruActionProvider
# from .schemas import SwapParams, LimitOrderParams, TokenAmount
# from .constants import DEFAULT_RPC_URLS

# def kuru_action_provider(rpc_url_by_chain_id: Optional[Dict[int, str]] = None) -> KuruActionProvider:
#     """
#     Create a Kuru action provider
    
#     Args:
#         rpc_url_by_chain_id: Optional mapping of chain IDs to RPC URLs
        
#     Returns:
#         A configured KuruActionProvider instance
#     """
#     # If RPC URLs weren't provided, use defaults
#     if rpc_url_by_chain_id is None:
#         rpc_url_by_chain_id = DEFAULT_RPC_URLS
    
#     return KuruActionProvider(rpc_url_by_chain_id=rpc_url_by_chain_id)

# __all__ = [
#     "KuruActionProvider",
#     "kuru_action_provider",
#     "SwapParams",
#     "LimitOrderParams",
#     "TokenAmount"
# ]