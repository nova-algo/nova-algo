from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass
from driftpy.types import MarketType
from driftpy.dlob.dlob_node import DLOBNode  
from decimal import Decimal

MakerNodeMap = dict[str, list[DLOBNode]]


class Bot(ABC):
    @abstractmethod
    async def init(self):
        pass

    @abstractmethod
    async def reset(self):
        pass

    @abstractmethod
    async def start_interval_loop(self, interval_ms: Optional[int] = 1000):
        pass

    @abstractmethod
    async def health_check(self):
        pass


@dataclass
class BotConfig:
    bot_id: str
    strategy_type: str
    market_indexes: list[int]
    sub_accounts: list[int]
    market_type: MarketType
    symbol: str
    timeframe: str
    # target_leverage: float = 1.0
    # spread: float = 0.0
    # max_positions: int = 1
    # size_multiplier: float = 1.0
    #additional_params: dict = field(default_factory=dict)


@dataclass
class MarketMakerConfig(BotConfig):
    max_position_size: Decimal
    order_size: Decimal
    num_levels: int
    base_spread: Decimal
    risk_factor: Decimal
    inventory_target: Decimal


@dataclass
class BollingerBandsConfig(BotConfig):
    # market_indexes: list[int]
    # sub_accounts: list[int]
    sma_window: int
    lookback_days: int
    max_positions: int
    max_loss: float
    target_profit: float
    size_multiplier: float
    # market_type: MarketType
    target_leverage: float = 1.0
    spread: float = 0.0
    # symbol: str
    # timeframe: str


@dataclass
class TrendFollowingConfig(BotConfig):
    # market_indexes: list[int]
    # sub_accounts: list[int]
    # market_type: MarketType
    target_leverage: float = 1.0
    spread: float = 0.0


# @dataclass
# class PerpFillerConfig(BotConfig):
#     filler_polling_interval: Optional[float] = None
#     revert_on_failure: bool = False
#     simulate_tx_for_cu_estimate: bool = False
#     use_burst_cu_limit: bool = False