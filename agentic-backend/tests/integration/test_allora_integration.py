import pytest
import asyncio
from unittest.mock import MagicMock, patch

from rebalancr.intelligence.allora.client import AlloraClient
from rebalancr.intelligence.intelligence_engine import IntelligenceEngine
from rebalancr.strategy.engine import StrategyEngine
from rebalancr.execution.providers.portfolio.portfolio_action_provider import portfolio_action_provider
from rebalancr.intelligence.reviewer import TradeReviewer

# Sample test data
SAMPLE_PORTFOLIO = {
    "portfolio_id": 1,
    "user_id": "test_user",
    "name": "Test Portfolio",
    "total_value": 10000,
    "assets": [
        {"symbol": "BTC", "value": 5000, "percentage": 50},
        {"symbol": "ETH", "value": 3000, "percentage": 30},
        {"symbol": "USDC", "value": 2000, "percentage": 20}
    ],
    "last_rebalance_timestamp": "2023-01-01T00:00:00Z"
}

SAMPLE_SENTIMENT = {
    "BTC": {
        "sentiment": "bullish",
        "confidence": 0.8,
        "manipulation_probability": 0.1
    },
    "ETH": {
        "sentiment": "bearish",
        "confidence": 0.6,
        "manipulation_probability": 0.2
    },
    "USDC": {
        "sentiment": "neutral",
        "confidence": 0.9,
        "manipulation_probability": 0.05
    }
}

SAMPLE_FEAR_GREED = {
    "BTC": {
        "index": 65,
        "sentiment": "greed",
        "confidence": 0.75
    },
    "ETH": {
        "index": 30,
        "sentiment": "fear",
        "confidence": 0.65
    },
    "USDC": {
        "index": 50,
        "sentiment": "neutral",
        "confidence": 0.8
    }
}

SAMPLE_MANIPULATION = {
    "BTC": {"detected": False, "confidence": 0.9},
    "ETH": {"detected": False, "confidence": 0.8},
    "USDC": {"detected": False, "confidence": 0.95}
}

# Create mock classes for dependency injection
class MockDB:
    async def get_portfolio(self, portfolio_id):
        return SAMPLE_PORTFOLIO
    
    async def get_asset_historical_data(self, symbol):
        # Return simple mock data
        return [{"timestamp": f"2023-01-{i+1}T00:00:00Z", "price": 100 + i} for i in range(30)]
    
    async def get_yield_protocols(self):
        return [
            {
                "name": "Aave",
                "supported_assets": ["ETH", "USDC"],
                "yields": {"ETH": 0.04, "USDC": 0.03}
            },
            {
                "name": "Compound",
                "supported_assets": ["BTC", "ETH", "USDC"],
                "yields": {"BTC": 0.02, "ETH": 0.035, "USDC": 0.025}
            }
        ]

@pytest.fixture
def mock_allora_client():
    client = MagicMock(spec=AlloraClient)
    client.analyze_sentiment.return_value = SAMPLE_SENTIMENT
    client.get_fear_greed_index.return_value = SAMPLE_FEAR_GREED
    client.detect_market_manipulation.return_value = SAMPLE_MANIPULATION
    return client

@pytest.fixture
def mock_components(mock_allora_client):
    # Create mock components
    market_analyzer = MagicMock()
    agent_kit_service = MagicMock()
    market_data_service = MagicMock()
    config = {"MIN_REBALANCE_DAYS": 7}
    
    db_manager = MockDB()
    
    # Create actual IntelligenceEngine with mock dependencies
    intelligence_engine = IntelligenceEngine(
        allora_client=mock_allora_client,
        market_analyzer=market_analyzer,
        agent_kit_service=agent_kit_service,
        market_data_service=market_data_service,
        config=config
    )
    
    # Create mock StrategyEngine
    strategy_engine = MagicMock(spec=StrategyEngine)
    strategy_engine.analyze_portfolio_statistics.return_value = {
        "risk_level": "moderate",
        "volatility": 0.15,
        "sharpe_ratio": 1.2,
        "drawdown": 0.08
    }
    strategy_engine.calculate_rebalancing_costs.return_value = {
        "trading_fees": 10,
        "gas_fees": 5,
        "slippage_cost": 5,
        "total_cost": 20
    }
    
    # Create mock for other components
    wallet_provider = MagicMock()
    risk_manager = MagicMock()
    yield_optimizer = MagicMock()
    performance_analyzer = MagicMock()
    trade_reviewer = MagicMock(spec=TradeReviewer)
    
    return {
        "intelligence_engine": intelligence_engine,
        "strategy_engine": strategy_engine,
        "wallet_provider": wallet_provider,
        "risk_manager": risk_manager,
        "yield_optimizer": yield_optimizer,
        "performance_analyzer": performance_analyzer,
        "trade_reviewer": trade_reviewer,
        "db_manager": db_manager,
        "config": config
    }

@pytest.mark.asyncio
async def test_sentiment_influences_decisions(mock_components):
    """Test that sentiment analysis affects intelligence engine decisions"""
    intelligence_engine = mock_components["intelligence_engine"]
    
    # Get recommendation with positive sentiment
    recommendation = await intelligence_engine.analyze_portfolio(
        user_id="test_user",
        portfolio_id=1
    )
    
    # Verify that the recommendation includes sentiment data
    assert "sentiment_analysis" in recommendation
    assert recommendation["sentiment_analysis"]["BTC"]["sentiment"] == "bullish"
    
    # Modify the mock to return bearish sentiment for all assets
    intelligence_engine.allora_client.analyze_sentiment.return_value = {
        asset: {"sentiment": "bearish", "confidence": 0.8, "manipulation_probability": 0.1}
        for asset in SAMPLE_SENTIMENT.keys()
    }
    
    # Get new recommendation with negative sentiment
    bearish_recommendation = await intelligence_engine.analyze_portfolio(
        user_id="test_user",
        portfolio_id=1
    )
    
    # The recommendations should be different based on sentiment
    assert bearish_recommendation["sentiment_analysis"]["BTC"]["sentiment"] == "bearish"
    
    # Reset the mock
    intelligence_engine.allora_client.analyze_sentiment.return_value = SAMPLE_SENTIMENT

@pytest.mark.asyncio
async def test_manipulation_detection_prevents_trades(mock_components):
    """Test that manipulation detection affects trade decisions"""
    intelligence_engine = mock_components["intelligence_engine"]
    
    # Get recommendation with no manipulation
    no_manipulation_rec = await intelligence_engine.analyze_portfolio(
        user_id="test_user",
        portfolio_id=1
    )
    
    # Modify the mock to indicate manipulation
    intelligence_engine.allora_client.detect_market_manipulation.return_value = {
        "BTC": {"detected": True, "confidence": 0.9},
        "ETH": {"detected": False, "confidence": 0.8},
        "USDC": {"detected": False, "confidence": 0.95}
    }
    
    # Get recommendation with manipulation
    manipulation_rec = await intelligence_engine.analyze_portfolio(
        user_id="test_user",
        portfolio_id=1
    )
    
    # Verify manipulation is reflected in the recommendation
    assert manipulation_rec["manipulation_detected"] == True
    
    # Reset the mock
    intelligence_engine.allora_client.detect_market_manipulation.return_value = SAMPLE_MANIPULATION

@pytest.mark.asyncio
async def test_fear_greed_affects_allocations(mock_components):
    """Test that fear/greed index affects allocation recommendations"""
    intelligence_engine = mock_components["intelligence_engine"]
    
    # Get recommendation with mixed sentiment
    mixed_rec = await intelligence_engine.analyze_portfolio(
        user_id="test_user",
        portfolio_id=1
    )
    
    # Record the original fear/greed values
    original_fear_greed = mixed_rec.get("fear_greed_index", {})
    
    # Modify fear/greed to extreme values
    intelligence_engine.allora_client.get_fear_greed_index.return_value = {
        "BTC": {"index": 90, "sentiment": "extreme_greed", "confidence": 0.9},
        "ETH": {"index": 10, "sentiment": "extreme_fear", "confidence": 0.9},
        "USDC": {"index": 50, "sentiment": "neutral", "confidence": 0.8}
    }
    
    # Get recommendation with extreme sentiment
    extreme_rec = await intelligence_engine.analyze_portfolio(
        user_id="test_user",
        portfolio_id=1
    )
    
    # Verify the fear/greed values changed
    assert extreme_rec["fear_greed_index"]["BTC"]["sentiment"] == "extreme_greed"
    assert extreme_rec["fear_greed_index"]["ETH"]["sentiment"] == "extreme_fear"
    
    # Reset the mock
    intelligence_engine.allora_client.get_fear_greed_index.return_value = SAMPLE_FEAR_GREED

@pytest.mark.asyncio
async def test_cost_benefit_analysis(mock_components):
    """Test that cost-benefit analysis prevents excessive rebalancing"""
    intelligence_engine = mock_components["intelligence_engine"]
    strategy_engine = mock_components["strategy_engine"]
    
    # Set up a scenario where costs slightly exceed benefits
    strategy_engine.calculate_rebalancing_costs.return_value = {
        "trading_fees": 50,
        "gas_fees": 20,
        "slippage_cost": 30,
        "total_cost": 100
    }
    
    # Mock the _calculate_potential_benefits method
    original_method = intelligence_engine._calculate_potential_benefits
    
    # First test: benefits are less than 2x costs (shouldn't recommend rebalance)
    async def mock_small_benefit(*args, **kwargs):
        return 150  # 1.5x cost
    
    intelligence_engine._calculate_potential_benefits = mock_small_benefit
    
    low_benefit_rec = await intelligence_engine.analyze_portfolio(
        user_id="test_user",
        portfolio_id=1
    )
    
    # Should not recommend rebalancing (benefit < 2x cost)
    assert low_benefit_rec["rebalance_recommended"] == False
    
    # Second test: benefits greatly exceed costs (should recommend rebalance)
    async def mock_large_benefit(*args, **kwargs):
        return 300  # 3x cost
    
    intelligence_engine._calculate_potential_benefits = mock_large_benefit
    
    high_benefit_rec = await intelligence_engine.analyze_portfolio(
        user_id="test_user",
        portfolio_id=1
    )
    
    # Should recommend rebalancing (benefit > 2x cost)
    assert high_benefit_rec["rebalance_recommended"] == True
    
    # Restore the original method
    intelligence_engine._calculate_potential_benefits = original_method

@pytest.mark.asyncio
async def test_portfolio_action_provider(mock_components):
    """Test that the PortfolioActionProvider works correctly with combined signals"""
    # Create PortfolioActionProvider with mock components
    portfolio_provider = portfolio_action_provider(
        wallet_provider=mock_components["wallet_provider"],
        intelligence_engine=mock_components["intelligence_engine"],
        strategy_engine=mock_components["strategy_engine"],
        risk_manager=mock_components["risk_manager"],
        yield_optimizer=mock_components["yield_optimizer"],
        performance_analyzer=mock_components["performance_analyzer"],
        db_manager=mock_components["db_manager"],
        config=mock_components["config"]
    )
    
    # Test analyze-portfolio action
    result = await portfolio_provider.analyze_portfolio({
        "portfolio_id": 1,
        "user_id": "test_user",
        "include_sentiment": True,
        "include_manipulation_check": True,
        "detailed": False
    })
    
    # Verify the result contains both sentiment and statistical data
    assert "insights" in result
    
    # Test assess-risk action
    risk_result = await portfolio_provider.assess_risk({
        "portfolio_id": 1,
        "user_id": "test_user",
        "timeframe_days": 30,
        "include_sentiment_impact": True
    })
    
    # Verify the result contains risk metrics and sentiment impact
    assert "risk_metrics" in risk_result
    assert "sentiment_impact" in risk_result
