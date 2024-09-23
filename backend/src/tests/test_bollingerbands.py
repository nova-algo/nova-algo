import pytest
from unittest.mock import AsyncMock, MagicMock
from src.strategy.bollingerbands import BollingerBandsStrategy
from src.common.types import BollingerBandsConfig
from driftpy.types import MarketType

@pytest.fixture
def mock_drift_api():
    return AsyncMock()

@pytest.fixture
def strategy_config():
    return BollingerBandsConfig(
        bot_id="test_bot",
        market_indexes=[0],
        sub_accounts=[0],
        sma_window=20,
        lookback_days=1,
        max_positions=1,
        market_type=MarketType.Perp(),
        target_leverage=3.0,
        spread=0.001,
        max_loss=-10.0,
        target_profit=5.0,
        size_multiplier=0.5,
        symbol="TEST-PERP",
        timeframe="15m"
    )

@pytest.mark.asyncio
async def test_bollinger_bands_strategy_initialize(mock_drift_api, strategy_config):
    mock_drift_api.get_market_index_by_symbol.return_value = 1

    strategy = BollingerBandsStrategy(mock_drift_api, strategy_config)
    await strategy.initialize()

    assert strategy.market_index == 1
    mock_drift_api.get_market_index_by_symbol.assert_called_once_with("TEST-PERP")

@pytest.mark.asyncio
async def test_bollinger_bands_strategy_execute(mock_drift_api, strategy_config):
    mock_drift_api.get_position_and_maxpos.return_value = ([], False, 0, None, 0, 0, None, 0)
    mock_drift_api.adjust_leverage_size_signal.return_value = (3.0, 100)
    mock_drift_api.get_market.return_value = MagicMock(bids=[MagicMock(price=100)], asks=[MagicMock(price=101)])

    strategy = BollingerBandsStrategy(mock_drift_api, strategy_config)
    strategy.market_index = 1
    strategy.fetch_ohlcv = MagicMock(return_value=MagicMock())
    strategy.calculate_bollinger_bands = MagicMock(return_value=(MagicMock(), True, False))

    await strategy.execute()

    mock_drift_api.get_position_and_maxpos.assert_called_once_with(1, 1)
    mock_drift_api.adjust_leverage_size_signal.assert_called_once_with(1, 3.0)
    mock_drift_api.get_market.assert_called_once_with(1)
    strategy.fetch_ohlcv.assert_called_once_with(500)
    strategy.calculate_bollinger_bands.assert_called_once()
    mock_drift_api.cancel_all_orders.assert_called_once()
    assert mock_drift_api.limit_order.call_count == 2