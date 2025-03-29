import asyncio
import pandas as pd
import numpy as np
from decimal import Decimal
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from src.strategy.marketmaking import MarketMaker
from src.api.drift.api import DriftAPI

class MockDriftAPI(DriftAPI):
    """
    A mock version of DriftAPI for backtesting purposes.
    """
    def __init__(self, historical_data: pd.DataFrame):
        self.historical_data = historical_data
        self.current_index = 0
        self.current_position = Decimal('0')
        self.current_orders: Dict[int, Dict] = {}
        self.order_id_counter = 1

    async def get_market_index_by_symbol(self, symbol: str) -> int:
        return 0  # Mock market index

    def get_market(self, market_index: int):
        class MockMarket:
            def __init__(self, oracle_price):
                self.oracle_price = oracle_price
        
        return MockMarket(int(self.historical_data.iloc[self.current_index]['price'] * 1e6))

    async def get_position(self, market_index: int):
        class MockPosition:
            def __init__(self, base_asset_amount):
                self.base_asset_amount = base_asset_amount
        
        return MockPosition(int(self.current_position * 1e9))

    async def cancel_all_orders(self):
        self.current_orders.clear()

    async def place_order(self, order_params):
        order_id = self.order_id_counter
        self.order_id_counter += 1
        self.current_orders[order_id] = {
            'price': order_params.price,
            'size': order_params.base_asset_amount,
            'direction': order_params.direction
        }
        return type('MockOrderResult', (), {'order_id': order_id})()

class Backtester:
    def __init__(self, historical_data: pd.DataFrame, market_maker: MarketMaker):
        self.historical_data = historical_data
        self.market_maker = market_maker
        self.mock_api = MockDriftAPI(historical_data)
        self.market_maker.api = self.mock_api
        self.trades: List[Dict] = []
        self.pnl_history: List[Decimal] = []

    async def run_backtest(self):
        await self.market_maker.initialize()

        for i in range(len(self.historical_data)):
            self.mock_api.current_index = i
            current_price = Decimal(str(self.historical_data.iloc[i]['price']))
            
            # Update market maker
            await self.market_maker.update_order_book()
            await self.market_maker.update_position()
            await self.market_maker.manage_inventory()
            await self.market_maker.place_orders()

            # Check for executed orders
            executed_orders = self.check_order_execution(current_price)
            for order in executed_orders:
                self.process_trade(order, current_price)

            # Calculate and record PnL
            pnl = self.calculate_pnl(current_price)
            self.pnl_history.append(pnl)

        return self.generate_backtest_results()

    def check_order_execution(self, current_price: Decimal) -> List[Dict]:
        executed_orders = []
        for order_id, order in list(self.mock_api.current_orders.items()):
            order_price = Decimal(str(order['price'])) / Decimal('1e6')
            if (order['direction'] == 'long' and current_price <= order_price) or \
               (order['direction'] == 'short' and current_price >= order_price):
                executed_orders.append(order)
                del self.mock_api.current_orders[order_id]
        return executed_orders

    def process_trade(self, order: Dict, execution_price: Decimal):
        size = Decimal(str(order['size'])) / Decimal('1e9')
        direction = 1 if order['direction'] == 'long' else -1
        self.mock_api.current_position += size * direction
        self.trades.append({
            'timestamp': self.historical_data.iloc[self.mock_api.current_index]['timestamp'],
            'price': execution_price,
            'size': size,
            'direction': order['direction']
        })

    def calculate_pnl(self, current_price: Decimal) -> Decimal:
        position_value = self.mock_api.current_position * current_price
        realized_pnl = sum((t['price'] - current_price) * t['size'] * (-1 if t['direction'] == 'long' else 1) 
                           for t in self.trades)
        return position_value + realized_pnl

    def generate_backtest_results(self) -> Dict:
        total_trades = len(self.trades)
        final_pnl = self.pnl_history[-1] if self.pnl_history else Decimal('0')
        sharpe_ratio = self.calculate_sharpe_ratio()
        max_drawdown = self.calculate_max_drawdown()

        return {
            'total_trades': total_trades,
            'final_pnl': final_pnl,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'pnl_history': self.pnl_history,
            'trades': self.trades
        }

    def calculate_sharpe_ratio(self) -> float:
        returns = pd.Series(self.pnl_history).pct_change().dropna()
        return float(returns.mean() / returns.std() * np.sqrt(252))  # Annualized Sharpe Ratio

    def calculate_max_drawdown(self) -> float:
        pnl_series = pd.Series(self.pnl_history)
        return float((pnl_series.cummax() - pnl_series).max() / pnl_series.cummax().max())

async def main():
    # Load historical data (you would need to implement this function)
    historical_data = load_historical_data('SOL-PERP', start_date='2023-01-01', end_date='2023-12-31')

    mock_api = MockDriftAPI(historical_data)
    market_maker = MarketMaker(
        api=mock_api,
        symbol="SOL-PERP",
        max_position_size=Decimal('100'),
        order_size=Decimal('1'),
        num_levels=5,
        spread=Decimal('0.001'),  # 0.1% initial spread
        risk_factor=Decimal('0.005'),
        inventory_target=Decimal('0')
    )

    backtester = Backtester(historical_data, market_maker)
    results = await backtester.run_backtest()

    print("Backtest Results:")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Final PnL: ${results['final_pnl']:.2f}")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {results['max_drawdown']:.2%}")

    # You can further analyze and visualize the results here

def load_historical_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    # This is a placeholder function. In a real implementation, you would
    # load actual historical data from a database or API.
    dates = pd.date_range(start=start_date, end=end_date, freq='5T')
    prices = np.random.randn(len(dates)).cumsum() + 100  # Random walk starting at 100
    return pd.DataFrame({
        'timestamp': dates,
        'price': np.maximum(prices, 1)  # Ensure prices are positive
    })

if __name__ == "__main__":
    asyncio.run(main())