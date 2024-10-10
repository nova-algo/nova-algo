import asyncio
import pandas as pd
import numpy as np
from decimal import Decimal
from typing import List, Dict, Tuple
from datetime import datetime, date, timedelta
from io import StringIO
import requests
import csv
import matplotlib.pyplot as plt

# Constants from the original code
BASE_PRECISION = 10**6
PRICE_PRECISION = 10**6

# Mock DriftAPI class for backtesting
class MockDriftAPI:
    def __init__(self):
        self.orders = []
        self.position = Decimal('0')
        self.current_price = Decimal('0')

    async def place_order_and_get_order_id(self, order_params):
        self.orders.append(order_params)
        return "mock_tx_sig", len(self.orders)

    async def cancel_all_orders(self):
        self.orders = []

    def get_market_price_data(self, market_index, market_type):
        class PriceData:
            def __init__(self, price):
                self.price = price
        return PriceData(int(self.current_price * PRICE_PRECISION))

    async def get_position(self, market_index, market_type=None):
        class Position:
            def __init__(self, base_asset_amount):
                self.base_asset_amount = base_asset_amount
        return Position(int(self.position * BASE_PRECISION))

# Function to get historical trade data (from the provided code)
def get_trades_for_range(account_key, start_date, end_date):
    """Retrieves trades for a given account and date range."""
    all_trades = []
    current_date = start_date
    while current_date <= end_date:
        year = current_date.year
        month = current_date.month
        day = current_date.day
        url = f"https://drift-historical-data-v2.s3.eu-west-1.amazonaws.com/program/dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH/user/{account_key}/tradeRecords/{year}/{year}{month:02}{day:02}"
        response = requests.get(url)
        response.raise_for_status()
        # Parse CSV data
        csv_data = StringIO(response.text)
        reader = csv.reader(csv_data)
        next(reader)  # Skip header
        for row in reader:
            all_trades.append(row)  # Add each row to the list
        current_date += timedelta(days=1)
    return all_trades

# MarketMaker class (simplified for backtesting)
class MarketMaker:
    def __init__(self, drift_api, config):
        self.drift_api = drift_api
        self.config = config
        self.market_index = config.market_indexes[0]
        self.position_size = Decimal('0')
        self.last_trade_price = None
        self.order_book = {'bids': [], 'asks': []}
        self.vwap = None
        self.volatility = Decimal('0.01')
        self.price_history: List[Decimal] = []

    async def update_position(self):
        position = await self.drift_api.get_position(self.market_index)
        if position:
            self.position_size = Decimal(str(position.base_asset_amount)) / BASE_PRECISION
        else:
            self.position_size = Decimal('0')

    def calculate_dynamic_spread(self) -> Decimal:
        spread = self.config.base_spread
        inventory_risk = abs(self.position_size - self.config.inventory_target) / self.config.max_position_size
        spread += self.config.risk_factor * inventory_risk
        if self.last_trade_price:
            market_price_data = self.drift_api.get_market_price_data(self.market_index, self.config.market_type)
            current_price = Decimal(str(market_price_data.price)) / PRICE_PRECISION
            price_change = abs(current_price - self.last_trade_price) / self.last_trade_price
            spread += price_change * Decimal('0.5')
        return spread

    def calculate_order_prices(self) -> Tuple[List[Decimal], List[Decimal]]:
        spread = self.calculate_dynamic_spread()
        market_price_data = self.drift_api.get_market_price_data(self.market_index, self.config.market_type)
        mid_price = Decimal(str(market_price_data.price)) / PRICE_PRECISION
        half_spread = spread / 2
        buy_prices = [mid_price - half_spread - Decimal('0.01') * i for i in range(self.config.num_levels)]
        sell_prices = [mid_price + half_spread + Decimal('0.01') * i for i in range(self.config.num_levels)]
        return buy_prices, sell_prices

    async def place_orders(self):
        await self.drift_api.cancel_all_orders()
        buy_prices, sell_prices = self.calculate_order_prices()
        for i in range(self.config.num_levels):
            buy_params = {
                'direction': 'Long',
                'base_asset_amount': int(self.config.order_size * BASE_PRECISION),
                'price': int(buy_prices[i] * PRICE_PRECISION),
            }
            await self.drift_api.place_order_and_get_order_id(buy_params)
            sell_params = {
                'direction': 'Short',
                'base_asset_amount': int(self.config.order_size * BASE_PRECISION),
                'price': int(sell_prices[i] * PRICE_PRECISION),
            }
            await self.drift_api.place_order_and_get_order_id(sell_params)

    async def update_market_data(self, price):
        self.drift_api.current_price = price
        self.last_trade_price = price
        await self.update_position()
        self.price_history.append(price)
        if len(self.price_history) > 20:
            self.price_history.pop(0)
        if len(self.price_history) >= 2:
            returns = [float(price / self.price_history[i - 1] - 1) for i, price in enumerate(self.price_history) if i > 0]
            self.volatility = Decimal(str(np.std(returns) * np.sqrt(len(returns))))

# Backtesting function
async def backtest(trades: List[List[str]], config):
    """
    Backtest the market maker strategy using historical trade data.
    
    :param trades: List of trades from historical data
    :param config: Configuration for the market maker
    :return: Dictionary containing backtest results
    """
    # Initialize mock API and market maker
    mock_api = MockDriftAPI()
    market_maker = MarketMaker(mock_api, config)

    # Prepare data structures for tracking results
    pnl = Decimal('0')
    position = Decimal('0')
    fees = Decimal('0')
    trade_count = 0
    inventory_history = []
    pnl_history = []
    price_history = []

    # Iterate through trades
    for trade in trades:
        # Extract relevant data from trade
        timestamp = datetime.fromtimestamp(int(trade[0]) / 1000)
        price = Decimal(trade[3])
        size = Decimal(trade[4])
        taker_side = trade[7]

        # Update market maker's view of the market
        await market_maker.update_market_data(price)

        # Place new orders
        await market_maker.place_orders()

        # Check if any orders were filled
        for order in mock_api.orders:
            if (taker_side == 'sell' and order['direction'] == 'Long' and order['price'] >= price) or \
               (taker_side == 'buy' and order['direction'] == 'Short' and order['price'] <= price):
                # Order filled
                fill_size = min(size, Decimal(order['base_asset_amount']) / BASE_PRECISION)
                fill_price = Decimal(order['price']) / PRICE_PRECISION
                
                # Update position and calculate PNL
                old_position = position
                if order['direction'] == 'Long':
                    position += fill_size
                else:
                    position -= fill_size
                
                trade_pnl = (fill_price - price) * fill_size if order['direction'] == 'Long' else (price - fill_price) * fill_size
                pnl += trade_pnl

                # Calculate and add fees
                fee = fill_size * fill_price * Decimal('0.0005')  # Assuming 0.05% fee
                fees += fee
                pnl -= fee

                trade_count += 1

                # Update size for potential partial fills
                size -= fill_size
                if size <= 0:
                    break

        # Record history
        inventory_history.append((timestamp, float(position)))
        pnl_history.append((timestamp, float(pnl)))
        price_history.append((timestamp, float(price)))

    # Calculate final results
    final_pnl = pnl - fees
    sharpe_ratio = calculate_sharpe_ratio(pnl_history)
    max_drawdown = calculate_max_drawdown(pnl_history)

    results = {
        'final_pnl': final_pnl,
        'fees': fees,
        'trade_count': trade_count,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'inventory_history': inventory_history,
        'pnl_history': pnl_history,
        'price_history': price_history
    }

    return results

# Helper functions for calculating performance metrics
def calculate_sharpe_ratio(pnl_history: List[Tuple[datetime, float]]) -> float:
    """
    Calculate the Sharpe ratio of the strategy.
    
    :param pnl_history: List of tuples containing timestamps and cumulative PnL
    :return: Sharpe ratio
    """
    returns = [pnl_history[i][1] - pnl_history[i-1][1] for i in range(1, len(pnl_history))]
    if not returns:
        return 0.0
    return float(np.mean(returns) / np.std(returns) * np.sqrt(252))  # Assuming daily returns and 252 trading days per year

def calculate_max_drawdown(pnl_history: List[Tuple[datetime, float]]) -> float:
    """
    Calculate the maximum drawdown of the strategy.
    
    :param pnl_history: List of tuples containing timestamps and cumulative PnL
    :return: Maximum drawdown as a percentage
    """
    pnl_values = [pnl for _, pnl in pnl_history]
    peak = float('-inf')
    max_drawdown = 0
    for pnl in pnl_values:
        if pnl > peak:
            peak = pnl
        drawdown = (peak - pnl) / peak if peak > 0 else 0
        max_drawdown = max(max_drawdown, drawdown)
    return max_drawdown

# Function to plot backtest results
def plot_backtest_results(results: Dict):
    """
    Plot the backtest results.
    
    :param results: Dictionary containing backtest results
    """
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 18), sharex=True)

    # Plot price
    timestamps, prices = zip(*results['price_history'])
    ax1.plot(timestamps, prices, label='Price')
    ax1.set_ylabel('Price')
    ax1.legend()
    ax1.set_title('Market Price')

    # Plot inventory
    timestamps, inventory = zip(*results['inventory_history'])
    ax2.plot(timestamps, inventory, label='Inventory')
    ax2.set_ylabel('Inventory')
    ax2.legend()
    ax2.set_title('Market Maker Inventory')

    # Plot PnL
    timestamps, pnl = zip(*results['pnl_history'])
    ax3.plot(timestamps, pnl, label='PnL')
    ax3.set_ylabel('PnL')
    ax3.legend()
    ax3.set_title('Cumulative PnL')

    plt.xlabel('Time')
    plt.tight_layout()
    plt.show()

# Main function to run the backtest
async def main():
    # Configuration
    class Config:
        def __init__(self):
            self.market_indexes = [0]
            self.market_type = 'Perp'
            self.base_spread = Decimal('0.001')
            self.risk_factor = Decimal('0.005')
            self.inventory_target = Decimal('0')
            self.max_position_size = Decimal('100')
            self.order_size = Decimal('1')
            self.num_levels = 5

    config = Config()

    # Fetch historical data
    account_key = "C13FZykQfLXKuMAMh2iuG7JxhQqd8otujNRAgVETU6id"
    start_date = date(2024, 1, 24)
    end_date = date(2024, 1, 26)
    trades = get_trades_for_range(account_key, start_date, end_date)

    # Run backtest
    results = await backtest(trades, config)

    # Print results
    print(f"Final PnL: ${results['final_pnl']:.2f}")
    print(f"Total Fees: ${results['fees']:.2f}")
    print(f"Number of Trades: {results['trade_count']}")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {results['max_drawdown']:.2%}")

    # Plot results
    plot_backtest_results(results)

if __name__ == "__main__":
    asyncio.run(main())