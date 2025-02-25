# Installation Guide

This guide will help you set up Nova Algo's trading infrastructure on your system.

## Prerequisites

- Python 3.10 or higher
- Poetry for dependency management
- Node access for supported chains
- Environment configuration files

## Step-by-Step Installation

### 1. Clone the Repository
```bash
git clone https://github.com/nova-algo/nova-algo.git
cd nova-algo
```

### 2. Install Dependencies
```bash
poetry install
```

### 3. Environment Setup

Create a `.env` file in the root directory:

```env
# Node Configuration
ETH_NODE_HTTP=your_eth_node_http
ETH_NODE_WS=your_eth_node_ws
SOL_NODE_HTTP=your_solana_node_http
SOL_NODE_WS=your_solana_node_ws

# Contract Addresses
UNISWAP_FACTORY=0x...
CURVE_REGISTRY=0x...

# API Keys
BUILDER_API_KEY=your_builder_key

# Safety Parameters
MAX_SLIPPAGE=0.5
MIN_PROFIT_THRESHOLD=0.01
```

### 4. Strategy Configuration

Each strategy requires specific configuration in `config/`:

```bash
cp config/example.strategy.yaml config/your_strategy.yaml
```

Edit `your_strategy.yaml` with appropriate parameters.

### 5. Testing Setup

```bash
# Install test dependencies
poetry install --with test

# Run tests
poetry run pytest
```

### 6. Running the System

#### Development Mode
```bash
poetry run python -m nova_algo --mode dev
```

#### Production Mode
```bash
poetry run python -m nova_algo --mode prod
```

## Chain-Specific Setup

### Ethereum
- Requires archive node access
- MEV builder connections
- Gas price oracle configuration

### Solana
- RPC node with commitment: finalized
- Account subscription capabilities
- Program deployment permissions

## Monitoring Setup

1. Install monitoring tools:
```bash
poetry install --with monitoring
```

2. Start Prometheus:
```bash
docker-compose up -d prometheus
```

3. Configure Grafana dashboards (optional)

## Troubleshooting

Common issues and solutions:

1. **Node Connection Issues**
   - Verify node URLs
   - Check websocket connections
   - Ensure archive data access

2. **Dependency Conflicts**
   - Clear poetry cache
   - Update lock file
   - Check Python version

3. **Strategy Errors**
   - Verify configuration
   - Check log files
   - Test in simulation mode

## Security Notes

- Never commit `.env` files
- Use secure key management
- Regular security audits
- Monitor system logs

## Updates

To update the system:

```bash
git pull
poetry install
poetry run alembic upgrade head
```

## Support

For additional support:
- Check our [Documentation](https://docs.novaalgo.xyz)
- Join our [Discord](https://discord.gg/novaalgo)
- Email: [support@novaalgo.xyz](mailto:support@novaalgo.xyz) 