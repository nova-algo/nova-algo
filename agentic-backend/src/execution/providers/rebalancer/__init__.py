"""
Rebalancer Action Provider

This module provides actions for portfolio rebalancing, implementing the multi-layered
architecture that combines:
- AI sentiment analysis from Allora
- Statistical analysis from traditional financial methods
- Validation layer for trade approval
- Execution through Kuru DEX
"""

from rebalancr.execution.providers.kuru.kuru_action_provider import KuruActionProvider

# Expose a function that allows late importing
def get_rebalancer_provider(kuru_provider=None):
    from .rebalancer_action_provider import rebalancer_action_provider
    return lambda *args, **kwargs: rebalancer_action_provider(*args, kuru_provider=kuru_provider, **kwargs)

# Export only the function
__all__ = ["get_rebalancer_provider"] 