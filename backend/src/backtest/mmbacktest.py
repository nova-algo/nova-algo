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
    
    
    import pandas as pd
import numpy as np
from typing import List, Tuple, Dict
from decimal import Decimal
import matplotlib.pyplot as plt
from collections import deque

class Order:
    def __init__(self, price: float, size: float, side: str, timestamp: pd.Timestamp):
        self.price = price
        self.size = size
        self.side = side
        self.timestamp = timestamp

class SimulatedOrderBook:
    def __init__(self):
        self.bids = []
        self.asks = []

    def add_order(self, order: Order):
        if order.side == "Buy":
            self.bids.append(order)
            self.bids.sort(key=lambda x: (-x.price, x.timestamp))
        else:
            self.asks.append(order)
            self.asks.sort(key=lambda x: (x.price, x.timestamp))

    def remove_order(self, order: Order):
        if order.side == "Buy":
            self.bids.remove(order)
        else:
            self.asks.remove(order)

    def get_best_bid_ask(self) -> Tuple[float, float]:
        best_bid = self.bids[0].price if self.bids else 0
        best_ask = self.asks[0].price if self.asks else float('inf')
        return best_bid, best_ask

class MarketMakerBacktest:
    def __init__(self, historical_data: pd.DataFrame, config: Dict):
        self.historical_data = historical_data
        self.config = config
        self.order_book = SimulatedOrderBook()
        self.position = 0
        self.cash = config['initial_capital']
        self.inventory_value = 0
        self.trades = []
        self.pnl_history = []
        self.inventory_history = []

    def _skew(self) -> Tuple[float, float]:
        inventory_delta = self.position - self.config['inventory_target']
        base_skew = np.random.normal(0, 0.1)  # Simplified skew generation
        bid_skew = max(0, min(base_skew + inventory_delta / self.config['max_position_size'], 1))
        ask_skew = max(0, min(-base_skew - inventory_delta / self.config['max_position_size'], 1))
        return bid_skew, ask_skew

    def _prices(self, mid_price: float, bid_skew: float, ask_skew: float) -> Tuple[np.ndarray, np.ndarray]:
        spread = self.config['base_spread'] * (1 + np.abs(bid_skew - ask_skew))
        bid_prices = np.linspace(mid_price - spread/2, mid_price - spread*2, self.config['num_levels'])
        ask_prices = np.linspace(mid_price + spread/2, mid_price + spread*2, self.config['num_levels'])
        return bid_prices, ask_prices

    def _sizes(self, bid_skew: float, ask_skew: float) -> Tuple[np.ndarray, np.ndarray]:
        base_size = self.config['base_order_size']
        bid_sizes = np.linspace(base_size * (1 + bid_skew), base_size * (1 - bid_skew), self.config['num_levels'])
        ask_sizes = np.linspace(base_size * (1 + ask_skew), base_size * (1 - ask_skew), self.config['num_levels'])
        return bid_sizes, ask_sizes

    def generate_quotes(self, timestamp: pd.Timestamp, mid_price: float) -> List[Order]:
        bid_skew, ask_skew = self._skew()
        bid_prices, ask_prices = self._prices(mid_price, bid_skew, ask_skew)
        bid_sizes, ask_sizes = self._sizes(bid_skew, ask_skew)

        quotes = []
        for price, size in zip(bid_prices, bid_sizes):
            quotes.append(Order(price, size, "Buy", timestamp))
        for price, size in zip(ask_prices, ask_sizes):
            quotes.append(Order(price, size, "Sell", timestamp))
        return quotes

    def place_orders(self, quotes: List[Order]):
        for order in quotes:
            self.order_book.add_order(order)

    def cancel_orders(self):
        self.order_book.bids.clear()
        self.order_book.asks.clear()

    def match_trades(self, timestamp: pd.Timestamp, price: float, volume: float):
        remaining_volume = volume
        while remaining_volume > 0 and (self.order_book.bids or self.order_book.asks):
            if price <= self.order_book.bids[0].price:
                order = self.order_book.bids[0]
                trade_size = min(remaining_volume, order.size)
                self.execute_trade(timestamp, order.price, trade_size, "Sell")
                remaining_volume -= trade_size
                order.size -= trade_size
                if order.size == 0:
                    self.order_book.remove_order(order)
            elif price >= self.order_book.asks[0].price:
                order = self.order_book.asks[0]
                trade_size = min(remaining_volume, order.size)
                self.execute_trade(timestamp, order.price, trade_size, "Buy")
                remaining_volume -= trade_size
                order.size -= trade_size
                if order.size == 0:
                    self.order_book.remove_order(order)
            else:
                break

    def execute_trade(self, timestamp: pd.Timestamp, price: float, size: float, side: str):
        if side == "Buy":
            self.position += size
            self.cash -= price * size
        else:
            self.position -= size
            self.cash += price * size
        self.trades.append((timestamp, price, size, side))

    def calculate_pnl(self, current_price: float):
        self.inventory_value = self.position * current_price
        total_value = self.cash + self.inventory_value
        return total_value - self.config['initial_capital']

    def run_backtest(self):
        for _, row in self.historical_data.iterrows():
            timestamp, price, volume = row['timestamp'], row['price'], row['volume']
            
            # Cancel existing orders and place new ones
            self.cancel_orders()
            quotes = self.generate_quotes(timestamp, price)
            self.place_orders(quotes)
            
            # Match trades
            self.match_trades(timestamp, price, volume)
            
            # Calculate and record PnL and inventory
            pnl = self.calculate_pnl(price)
            self.pnl_history.append((timestamp, pnl))
            self.inventory_history.append((timestamp, self.position))

    def calculate_performance_metrics(self):
        pnl_df = pd.DataFrame(self.pnl_history, columns=['timestamp', 'pnl'])
        pnl_df.set_index('timestamp', inplace=True)
        
        total_pnl = pnl_df['pnl'].iloc[-1]
        sharpe_ratio = np.sqrt(252) * pnl_df['pnl'].pct_change().mean() / pnl_df['pnl'].pct_change().std()
        max_drawdown = (pnl_df['pnl'].cummax() - pnl_df['pnl']).max()
        
        inventory_df = pd.DataFrame(self.inventory_history, columns=['timestamp', 'inventory'])
        inventory_df.set_index('timestamp', inplace=True)
        
        avg_inventory = inventory_df['inventory'].mean()
        inventory_turnover = len(self.trades) / len(self.historical_data)
        
        return {
            'total_pnl': total_pnl,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'avg_inventory': avg_inventory,
            'inventory_turnover': inventory_turnover
        }

    def plot_results(self):
        pnl_df = pd.DataFrame(self.pnl_history, columns=['timestamp', 'pnl'])
        inventory_df = pd.DataFrame(self.inventory_history, columns=['timestamp', 'inventory'])
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
        
        ax1.plot(pnl_df['timestamp'], pnl_df['pnl'])
        ax1.set_title('Cumulative PnL')
        ax1.set_ylabel('PnL')
        
        ax2.plot(inventory_df['timestamp'], inventory_df['inventory'])
        ax2.set_title('Inventory Over Time')
        ax2.set_ylabel('Inventory')
        ax2.set_xlabel('Time')
        
        plt.tight_layout()
        plt.show()

# Usage example
def main():
    # Load historical data (you need to implement this part based on your data source)
    historical_data = pd.read_csv('historical_data.csv', parse_dates=['timestamp'])
    
    config = {
        'initial_capital': 100000,
        'base_spread': 0.001,
        'num_levels': 5,
        'base_order_size': 1,
        'inventory_target': 0,
        'max_position_size': 100
    }
    
    backtest = MarketMakerBacktest(historical_data, config)
    backtest.run_backtest()
    
    metrics = backtest.calculate_performance_metrics()
    print("Performance Metrics:")
    for key, value in metrics.items():
        print(f"{key}: {value}")
    
    backtest.plot_results()

if __name__ == "__main__":
    main()