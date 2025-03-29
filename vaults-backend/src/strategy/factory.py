from typing import Union
from src.api.drift.api import DriftAPI
from src.api.uniswap import UniswapAPI
from src.common.types import TrendFollowingConfig, BackrunnerConfig
from src.strategy.trendfollowing import TrendFollowingStrategy
from src.strategy.backrunner.strategy import BackrunnerStrategy

class StrategyFactory:
    @staticmethod
    def create_strategy(
        config: Union[TrendFollowingConfig, BackrunnerConfig],
        api: Union[DriftAPI, UniswapAPI]
    ):
        """Create strategy based on config type"""
        
        if isinstance(config, TrendFollowingConfig):
            if not isinstance(api, DriftAPI):
                raise ValueError("TrendFollowingStrategy requires DriftAPI")
            return TrendFollowingStrategy(config, api)
            
        elif isinstance(config, BackrunnerConfig):
            if not isinstance(api, UniswapAPI):
                raise ValueError("BackrunnerStrategy requires UniswapAPI")
            return BackrunnerStrategy(config, api)
            
        else:
            raise ValueError(f"Unknown strategy config type: {type(config)}")


# from src.common.types import BotConfig, MarketMakerConfig, TrendFollowingConfig
# #from src.strategy.bollingerbands import BollingerBandsStrategy
# from src.strategy.marketmaking import MarketMaker
# from src.strategy.trendfollowing import TrendFollowingStrategy
# from src.api.drift.api import DriftAPI

# class StrategyFactory:
#     @staticmethod
#     def create_strategy(config: BotConfig, drift_api: DriftAPI):
#         if config.strategy_type == "market_making":
#             if not isinstance(config, MarketMakerConfig):
#                 raise ValueError("MarketMakerConfig required for market_making strategy")
#             return MarketMaker(drift_api, config)
#         elif config.strategy_type == "trend_following":
#             if not isinstance(config, TrendFollowingConfig):
#                 raise ValueError("TrendFollowingConfig required for trend_following strategy")
#             return TrendFollowingStrategy(drift_api, config)
#         else:
#             raise ValueError(f"Unknown strategy type: {config.strategy_type}")