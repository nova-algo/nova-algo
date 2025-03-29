
# Nova Algo: Agentic Backend

> AI-powered trading agent and portfolio management component

This module provides Nova Algo with intelligent portfolio management and conversational trading capabilities through an AI-powered agentic system.

## 📋 Component Overview

The agentic backend powers these Nova Algo features:
- Conversational trading interface
- Autonomous portfolio rebalancing
- Market intelligence and risk assessment
- Strategy execution and optimization

## 🧠 Technical Architecture

The component is structured around three core systems:

1. **Intelligence Engine**
   - Statistical market analysis
   - Sentiment processing
   - Risk-adjusted portfolio optimization

2. **Agent Kit**
   - Natural language understanding
   - Trading intent recognition
   - Conversation management

3. **Strategy Engine**
   - Trade execution routing
   - Risk management
   - Performance tracking

## 📁 Directory Structure

```plaintext
agentic-backend/
├── src/
│   ├── intelligence/
│   │   ├── intelligence_engine.py    # Core analysis engine
│   │   ├── market_analysis.py        # Statistical analysis
│   │   ├── market_conditions.py      # Market classifier
│   │   └── allora/                   # Allora integration
│   ├── chat/                         # Conversational interface
│   ├── strategy/                     # Strategy implementation
│   │   ├── engine.py                 # Strategy execution
│   │   ├── risk_manager.py           # Risk assessment
│   │   └── risk_monitor.py           # Risk tracking
│   └── execution/                    # Trade execution
└── tests/                            # Component tests
```

## 💻 Code Examples

### Intelligence Engine
```python
class IntelligenceEngine:
    """Combines market analysis, AI predictions, and statistical metrics"""
    
    async def analyze_portfolio(self, user_id: str, portfolio_id: int):
        # Get portfolio data and market analysis
        # Calculate combined scores using asset-specific weights
        # Generate rebalancing recommendations
```

### Agent Communication
```python
class AgentKitClient:
    """Client for business logic and domain-specific operations"""
    
    async def get_agent_response(self, user_id, message, session_id=None):
        """
        Send a message and get a response
        """
        # Use the AgentManager to get the basic response
        response = await self.agent_manager.get_agent_response(user_id, message, session_id)
        
        # Here you could enrich the response with business context if needed
        # For example, adding market data or portfolio recommendations
        
        return response
```

## 🛠️ Development

### Setup
```bash
# Navigate to component directory
cd nova-algo/agentic-backend

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
- FastAPI for API endpoints
- LangChain for agent orchestration
- Allora for market sentiment analysis

## 🔄 Integration

This component integrates with:

1. **Nova Algo Core** - For strategy execution and account management
2. **Vaults Backend** - For automated trading strategies
3. **Frontend** - Through WebSocket and REST APIs

## 📊 Performance Testing

Run performance benchmarks to ensure the agent's response time stays under 1 second:

```bash
poetry run pytest tests/performance/ -v
```

## 📝 Development Notes

- The agent uses a ReAct pattern for reasoning about market conditions
- WebSocket connections maintain user chat sessions
- Agent responses are enriched with real-time market data
- All trading actions go through the risk management system
