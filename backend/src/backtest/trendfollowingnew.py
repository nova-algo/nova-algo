import ccxt
import pandas as pd
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def ALMA(series, window=40, sigma=9, offset=0.85):
    """Arnaud Legoux Moving Average"""
    size = series.size
    m = offset * (window - 1)
    s = window / sigma
    weights = np.exp(-((np.arange(window) - m) ** 2) / (2 * s ** 2))
    weights /= weights.sum()
    alma = np.convolve(series, weights, mode='same')
    return alma

class ALMAStrategy(Strategy):
    def init(self):
        self.alma = self.I(ALMA, self.data.Close, window=40)
        self.exhaustion_bar_count = 10  # Exhaustion Bar Count
        self.exhaustion_confirmed = False
    
    def next(self):
        # Check for exhaustion confirmation (relaxed logic)
        if len(self.data.Close) >= self.exhaustion_bar_count:
            recent_prices = self.data.Close[-self.exhaustion_bar_count:]
            uptrend = sum(recent_prices[i] <= recent_prices[i+1] for i in range(len(recent_prices)-1)) >= 7  # At least 7 out of 10 bars in uptrend
            downtrend = sum(recent_prices[i] >= recent_prices[i-1] for i in range(len(recent_prices)-1)) >= 7  # At least 7 out of 10 bars in downtrend
            
            if uptrend:
                self.exhaustion_confirmed = True  # Uptrend exhaustion
            elif downtrend:
                self.exhaustion_confirmed = True  # Downtrend exhaustion
            else:
                self.exhaustion_confirmed = False
        
        # Buy/Sell logic with exhaustion confirmation as a filter
        if crossover(self.data.Close, self.alma):  # Buy signal
            if self.exhaustion_confirmed:  # Only buy if exhaustion is confirmed
                self.buy(size=0.4)
        elif crossover(self.alma, self.data.Close):  # Sell signal
            if self.exhaustion_confirmed:  # Only sell if exhaustion is confirmed
                self.sell(size=0.1)

def fetch_data(symbol, timeframe, start_date, end_date):
    exchange = ccxt.bybit({'enableRateLimit': True})
    all_ohlcv = []
    current_date = pd.Timestamp(start_date)
    end_datetime = pd.Timestamp(end_date)
    
    while current_date < end_datetime:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, exchange.parse8601(current_date.isoformat()), limit=1000)
            all_ohlcv.extend(ohlcv)
            if len(ohlcv):
                current_date = pd.Timestamp(ohlcv[-1][0], unit='ms')
            else:
                current_date += pd.Timedelta(days=1)
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            break
    
    df = pd.DataFrame(all_ohlcv, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
    df.set_index('Timestamp', inplace=True)
    
    # Remove duplicate timestamps
    df = df[~df.index.duplicated(keep='first')]
    return df

def main():
    symbol = 'SOL/USDT'
    timeframe = '1h' 
    start_date = '2025-01-01T00:00:00'
    end_date = '2025-02-12T23:59:59'

    # Fetch historical data
    df = fetch_data(symbol, timeframe, start_date, end_date)

    # Initialize and run backtest
    bt = Backtest(df, ALMAStrategy, cash=100000, commission=.01, trade_on_close=True)
    stats = bt.run()

    # Print performance metrics
    print(stats)

    # Plot the results
    # bt.plot()

    # Plot equity curve
    plt.figure(figsize=(10, 6))
    plt.plot(stats['_equity_curve']['Equity'])
    plt.title('Equity Curve')
    plt.xlabel('Time')
    plt.ylabel('Equity')
    plt.show()

    # Plot trades
    sns.set(style="whitegrid")
    plt.figure(figsize=(10, 6))
    plt.scatter(stats['_trades']['EntryTime'], stats['_trades']['EntryPrice'], color='green', label='Buy')
    plt.scatter(stats['_trades']['ExitTime'], stats['_trades']['ExitPrice'], color='red', label='Sell')
    plt.title('Trades')
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.legend()
    plt.show()

if __name__ == "__main__":
    main()