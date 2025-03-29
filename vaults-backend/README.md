# Nova Algo: Vaults Backend

> Advanced algorithmic trading vaults and strategy execution component

This module provides Nova Algo with automated strategy vaults and algorithmic trading capabilities across multiple markets and assets.

## 📋 Component Overview

The vaults backend powers these Nova Algo features:
- Automated trading strategy execution
- Yield-generating vaults for user deposits
- Multi-asset support (USDC, BONK, etc.)
- Drift Protocol integration for Solana trading

## 🧠 Technical Architecture

The component is structured around three core systems:

1. **Strategy Engine**
   - Algorithm implementation and execution
   - Signal generation and analysis
   - Trade execution and management

2. **Vault Management**
   - User deposit handling
   - Asset allocation
   - Performance tracking
   - Fee distribution

3. **Market Integration**
   - Drift Protocol connectivity
   - Order routing and execution
   - Position management
   - Market data processing

## 📁 Directory Structure

```plaintext
vaults-backend/
├── src/
│   ├── strategy/
│   │   ├── trendfollowing.py        # Trend following algorithm
│   │   ├── marketmaking.py          # Market making algorithm
│   │   ├── backrunning.py           # MEV backrunner
│   │   └── factory.py               # Strategy factory
│   ├── api/
│   │   ├── drift/                   # Drift Protocol integration
│   │   │   ├── api.py               # Core Drift API
│   │   │   └── ws.py                # WebSocket connections
│   │   └── uniswap/                 # Ethereum integrations
│   ├── vault/
│   │   ├── configure_vault.py       # Vault configuration
│   │   ├── initialize_vault.py      # Vault initialization
│   │   └── manager.py               # Vault operations
│   └── common/
│       ├── types.py                 # Core data types
│       └── utils.py                 # Utility functions
└── tests/                           # Component tests
```

## 💻 Core Strategies

### Trend Following
```python
class TrendFollowingStrategy:
    """Advanced trend following strategy for perpetual markets"""
    
    async def execute(self):
        """Execute the strategy based on market conditions"""
        # Calculate ALMA indicator
        alma_value = self._calculate_alma(self.prices, self.alma_window)
        
        # Generate signal based on ALMA crossovers and volatility
        signal = self._generate_signal(alma_value, self.threshold)
        
        # Execute position with dynamic sizing
        if signal.direction != self.current_position.direction:
            await self._adjust_position(signal)
```

### Market Making
```python
class MarketMaker:
    """Liquidity provision and market making strategy"""
    
    async def execute(self):
        """Update and manage orders"""
        # Calculate bid/ask based on market microstructure
        bid, ask = self._calculate_quotes(self.order_book, self.volatility)
        
        # Dynamically adjust spread based on market conditions
        spread = self._calculate_dynamic_spread(self.volatility, self.volume)
        
        # Place and manage orders
        await self._manage_orders(bid, ask, spread)
```

## 🛠️ Development

### Setup
```bash
# Navigate to component directory
cd nova-algo/vaults-backend

# Install dependencies using Poetry
poetry install

# Configure environment
cp .env.example .env
# Edit .env with your API keys and settings

# Activate virtual environment
poetry shell

# Run component tests
poetry run pytest
```

### Key Dependencies
- Python 3.10+
- Drift Protocol SDK
- Solana Web3.py
- Pandas and Pandas-TA for technical analysis

## 🔄 Integration

This component integrates with:

1. **Agentic Backend** - For intelligent strategy selection and optimization
2. **Frontend** - For vault display, deposit UI, and performance tracking

## 📊 Performance Metrics

Each vault strategy tracks multiple performance metrics:

- Sharpe ratio (risk-adjusted returns)
- Maximum drawdown
- Win/loss ratio
- Profit factor
- Daily/monthly ROI

## 📝 Development Notes

- All strategies implement circuit breakers for market volatility protection
- Vaults support both USDC and native token deposits
- Strategy parameters are configurable through environment variables
- Performance metrics are stored for historical analysis and optimization
