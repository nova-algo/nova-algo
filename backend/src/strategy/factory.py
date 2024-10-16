from src.common.types import BotConfig, MarketMakerConfig, TrendFollowingConfig
#from src.strategy.bollingerbands import BollingerBandsStrategy
from src.strategy.marketmaking import MarketMaker
from src.strategy.trendfollowing import TrendFollowingStrategy
from src.api.drift.api import DriftAPI

class StrategyFactory:
    @staticmethod
    def create_strategy(config: BotConfig, drift_api: DriftAPI):
        if config.strategy_type == "market_making":
            if not isinstance(config, MarketMakerConfig):
                raise ValueError("MarketMakerConfig required for market_making strategy")
            return MarketMaker(drift_api, config)
        elif config.strategy_type == "trend_following":
            if not isinstance(config, TrendFollowingConfig):
                raise ValueError("TrendFollowingConfig required for trend_following strategy")
            return TrendFollowingStrategy(drift_api, config)
        else:
            raise ValueError(f"Unknown strategy type: {config.strategy_type}")