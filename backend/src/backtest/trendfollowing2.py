# Import these libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
#from mplfinance.original_flavor import candlestick_ohlc
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import ccxt

# Strategy Class Definition
class EnhancedALMAStrategy(Strategy):
    # Params
    exhaustion_swing_length = 40
    smoothing_factor = 5
    threshold_multiplier = 1.5
    atr_length = 14
    alma_offset = 0.85
    alma_sigma = 6
    pyramiding = 5
    
    def init(self):
        # Indicator setup + other extras
        self.alma = self.I(self.alma_calc, self.data.Close, self.exhaustion_swing_length, self.alma_offset, self.alma_sigma)
        self.smoothed_alma = self.I(lambda x: pd.Series(x).rolling(self.smoothing_factor).mean(), self.alma)
        self.atr = self.I(lambda x: pd.Series(x).rolling(self.atr_length).mean(), self.data.TR)
        self.dynamic_threshold = self.I(lambda x: pd.Series(x) * self.threshold_multiplier, self.atr)
        self.upper_band = self.I(lambda x, y: pd.Series(x) + pd.Series(y).rolling(self.exhaustion_swing_length).std() * 1.5, self.smoothed_alma, self.data.Close)
        self.lower_band = self.I(lambda x, y: pd.Series(x) - pd.Series(y).rolling(self.exhaustion_swing_length).std() * 1.5, self.smoothed_alma, self.data.Close)

    def alma_calc(self, price, window, offset, sigma):
        m = np.floor(offset * (window - 1))
        s = window / sigma
        w = np.exp(-((np.arange(window) - m) ** 2) / (2 * s * s))
        w /= w.sum()

        def alma(x):
            return (np.convolve(x, w[::-1], mode='valid'))[0]

        return pd.Series(price).rolling(window).apply(alma, raw=True)

    def next(self):
        price = self.data.Close[-1]
        
        # This is just to shorten the code and make it readable
        buy_condition = crossover(self.data.Close, self.smoothed_alma + self.dynamic_threshold)
        sell_condition = crossover(self.smoothed_alma - self.dynamic_threshold, self.data.Close)
        
        position_size = self.position.size

        position_size = self.position.size

        px_size = 0.75 # Never change it past 0.75 or you will go -ve

        if len(self.trades) >= self.pyramiding:
            return
        
        if buy_condition:
            if position_size < 1:
                self.position.close()
            self.buy(size=px_size)
        elif sell_condition:
            if position_size > 1:
                self.position.close()
            self.sell(size=px_size)

# Function to calculate True Range (used in ATR)
def calculate_true_range(df):
    df['Previous Close'] = df['Close'].shift(1)
    df['High-Low'] = df['High'] - df['Low']
    df['High-PrevClose'] = abs(df['High'] - df['Previous Close'])
    df['Low-PrevClose'] = abs(df['Low'] - df['Previous Close'])
    df['TR'] = df[['High-Low', 'High-PrevClose', 'Low-PrevClose']].max(axis=1)
    return df['TR']

# Function to calculate volatility (standard deviation of returns)
# It isn't required in the grand scheme but it is a nice to have
def calculate_volatility(df, window=14):
    df['Returns'] = df['Close'].pct_change()
    df['Volatility'] = df['Returns'].rolling(window).std()
    # Return the rolling standard deviation of returns
    
    return df['Volatility']

# Fetch historical data from Bybit (or another exchange, if you like)
def fetch_data(symbol, timeframe, start_date, end_date):
    exchange = ccxt.bybit({'enableRateLimit': True})
    
    timeframe_seconds = {
        '1m': 60, '5m': 300, '15m': 900, '30m': 1800,
        '1h': 3600, '4h': 14400, '1d': 86400
    }
    
    all_ohlcv = []
    current_date = pd.Timestamp(start_date).tz_localize(None)
    end_datetime = pd.Timestamp(end_date).tz_localize(None)
    
    while current_date < end_datetime:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, exchange.parse8601(current_date.isoformat()), limit=1000)
            all_ohlcv.extend(ohlcv)
            if len(ohlcv):
                current_date = pd.Timestamp(ohlcv[-1][0], unit='ms') + pd.Timedelta(seconds=timeframe_seconds[timeframe])
            else:
                current_date += pd.Timedelta(days=1)
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            break
    
    df = pd.DataFrame(all_ohlcv, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
    df = df.set_index('Timestamp')
    df['TR'] = calculate_true_range(df)
    return df

# Function to run the backtest and plot the results
def run_backtest(df, symbol):
    bt = Backtest(df, EnhancedALMAStrategy, cash=100000, commission=.002)
    stats = bt.run()
    
    # Print the stats to check available keys
    # print(f"Stats for {symbol}:")
    # print(stats)  # This will show you all the keys available in the stats dictionary

    # Calculate % return from day 1 to the final day
    initial_equity = stats['_equity_curve']['Equity'][0]
    final_equity = stats['_equity_curve']['Equity'][-1]
    total_return = (final_equity - initial_equity) / initial_equity * 100
    print(f"Total Return for {symbol}: {total_return:.2f}%")
    
    # Store results in a dictionary
    result = {
        'Symbol': symbol,
        'Total Return (%)': total_return,
        'Final Equity ($)': final_equity,
        'Initial Equity ($)': initial_equity,
        'Sharpe Ratio': stats['Sharpe Ratio'],
        'Buy and Hold Return (%)': stats['Buy & Hold Return [%]'],
        'Number of Trades': stats['# Trades'] if '# Trades' in stats else None,
        'Win Rate (%)': stats['Win Rate [%]'] if 'Win Rate [%]' in stats else None,
        'Max Drawdown (%)': stats['Max. Drawdown [%]'] if 'Max. Drawdown [%]' in stats else None
    }
    
    return result  # Return the result for each symbol

# Main function to execute the script
if __name__ == "__main__":
    symbols = ['SOLPERP', 'SOLUSDT']  # List of symbols to backtest
    timeframe = '15m' # You can change this time frame
    start_date = '2024-01-01T00:00:00Z' # You can also change this
    end_date = '2024-10-01T00:00:00Z' # And this

    results = []  # List to store results for each symbol

    for symbol in symbols: # Loop through each symbol and return the value into the results list
        df = fetch_data(symbol, timeframe, start_date, end_date)
        
        # Add ATR and Volatility to the dataframe
        df['ATR'] = calculate_true_range(df).rolling(14).mean()
        df['Volatility'] = calculate_volatility(df)
        
        
        # Run the backtest and store the results for each symbol
        result = run_backtest(df, symbol)
        results.append(result)  # Append the result to the list
        

    # Convert results to a DataFrame and display
    results_df = pd.DataFrame(results)
    print(results_df)
