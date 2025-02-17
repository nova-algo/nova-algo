from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, TypedDict
from dataclasses import dataclass
from driftpy.types import MarketType, PerpPosition, SpotPosition, PerpMarketAccount, SpotMarketAccount
from driftpy.dlob.dlob_node import DLOBNode  
from decimal import Decimal
from hexbytes import HexBytes

MakerNodeMap = dict[str, list[DLOBNode]]

PositionType = Union[PerpPosition, SpotPosition]

MarketAccountType = Union[PerpMarketAccount, SpotMarketAccount]


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
class TrendFollowingConfig(BotConfig):
    position_size: Decimal
    symbol: str
    market_type: MarketType
    market_indexes: list[int] # in milliseconds
    timeframe: str
    start_date: str
    end_date: str
    exhaustion_swing_length: int = 40
    smoothing_factor: int = 5
    threshold_multiplier: float = 1.5
    atr_length: int = 14
    alma_offset: float = 0.85
    alma_sigma: float = 6
    pyramiding: int = 5
    target_leverage: float = 1.0
    polling_interval: int = 60000 # in milliseconds

# @dataclass
# class PerpFillerConfig(BotConfig):
#     filler_polling_interval: Optional[float] = None
#     revert_on_failure: bool = False
#     simulate_tx_for_cu_estimate: bool = False
#     use_burst_cu_limit: bool = False


# @dataclass
# class BollingerBandsConfig(BotConfig):
#     # market_indexes: list[int]
#     # sub_accounts: list[int]
#     sma_window: int
#     lookback_days: int
#     max_positions: int
#     max_loss: float
#     target_profit: float
#     size_multiplier: float
#     # market_type: MarketType
#     target_leverage: float = 1.0
#     spread: float = 0.0
#     # symbol: str
#     # timeframe: str


# class SwapParams(TypedDict):
#     token_in: str
#     token_out: str
#     amount_in: Decimal
#     min_amount_out: Decimal
#     deadline: Optional[int]
#     slippage_tolerance: Decimal

# class LiquidityParams(TypedDict):
#     token_a: str
#     token_b: str
#     amount_a_desired: Decimal
#     amount_b_desired: Decimal
#     amount_a_min: Decimal
#     amount_b_min: Decimal
#     deadline: Optional[int]

# class TokenInfo(TypedDict):
#     address: str
#     symbol: str
#     decimals: int

@dataclass
class BackrunTx:
    tx: Dict
    raw: HexBytes 
    hash: HexBytes

@dataclass
class ArbitrageResult:
    profit_amount: int
    path: List[str]
    pools: Dict[str, Dict]
