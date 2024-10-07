from src.common.types import BotConfig, BollingerBandsConfig, MarketMakerConfig
from src.strategy.bollingerbands import BollingerBandsStrategy
from src.strategy.marketmaking import MarketMaker
#from src.strategy.trendfollowing import TrendFollowingStrategy
from src.api.drift.api import DriftAPI

class StrategyFactory:
    @staticmethod
    def create_strategy(config: BotConfig, drift_api: DriftAPI):
        if config.strategy_type == "bollinger_bands":
            if not isinstance(config, BollingerBandsConfig):
                raise ValueError("BollingerBandsConfig required for bollinger_bands strategy")
            return BollingerBandsStrategy(drift_api, config)
        elif config.strategy_type == "market_making":
            if not isinstance(config, MarketMakerConfig):
                raise ValueError("MarketMakerConfig required for market_making strategy")
            return MarketMaker(drift_api, config)
        else:
            raise ValueError(f"Unknown strategy type: {config.strategy_type}")