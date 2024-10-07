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
        sell_conditon = crossover(self.smoothed_alma - self.dynamic_threshold, self.data.Close)
        
        
        if len(self.trades) >= self.pyramiding:
            return
        position_size = self.position.size
        if buy_condition:
            if position_size < 1:
                self.position.close()
            self.buy(size=0.25)
        elif sell_conditon:
            if position_size > 1:
                self.position.close()
            self.sell(size=0.25)

# Function to calculate True Range (used in ATR)
def calculate_true_range(df):
    df['Previous Close'] = df['Close'].shift(1)
    df['High-Low'] = df['High'] - df['Low']
    df['High-PrevClose'] = abs(df['High'] - df['Previous Close'])
    df['Low-PrevClose'] = abs(df['Low'] - df['Previous Close'])
    df['TR'] = df[['High-Low', 'High-PrevClose', 'Low-PrevClose']].max(axis=1)
    return df['TR']

# Function to calculate volatility (standard deviation of returns)
# It isn't required in the granc scheme but it is a nice to have
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

'''
Function to plot candlestick chart with entry/exit points
# This isn't neceessary to be honest
def plot_candlestick_with_signals(df, trades, symbol):
    df['NumDate'] = mdates.date2num(df.index)
    
    fig, ax = plt.subplots(figsize=(20, 8))

    # Plot candlestick chart
    candlestick_ohlc(ax, df[['NumDate', 'Open', 'High', 'Low', 'Close']].values, width=0.6, colorup='green', colordown='red')
    
    # Plot entry and exit points
    buy_signals = trades.loc[trades['Size'] > 0]
    print(f'Buy Signals for {symbol}\n {buy_signals}')
    sell_signals = trades.loc[trades['Size'] < 0]
    print(f'Sell Signals for {symbol}\n {sell_signals}')
    
    # Plot buy/sell signals
    ax.scatter(df.index[buy_signals['EntryBar']], buy_signals['EntryPrice'], marker='^', color='green', label='Buy Entry', zorder=5)
    ax.scatter(df.index[sell_signals['EntryBar']], sell_signals['EntryPrice'], marker='v', color='red', label='Sell Entry', zorder=5)
    ax.scatter(df.index[trades['ExitBar']], trades['ExitPrice'], marker='x', color='black', label='Exit', zorder=5)
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    plt.title(f"Candlestick Chart with Buy/Sell Signals for {symbol}")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"candlestick_with_signals_{symbol}.png")
    plt.show()'''

# Function to plot ATR based Volatility
def plot_atr_and_volatility(df, symbol):
    plt.figure(figsize=(10, 6))
    plt.plot(df.index, df['ATR'], label="ATR", color='orange')
    plt.plot(df.index, df['Volatility'], label="Volatility", color='blue')
    plt.ylabel("Value")
    plt.title(f"ATR and Volatility for {symbol}")
    plt.legend()
    plt.savefig(f"atr_and_volatility_{symbol}.png")
    plt.show()

# Function to plot equity curve
def plot_equity_curve(stats, symbol):
    plt.figure(figsize=(10, 6))
    plt.plot(stats['_equity_curve']['Equity'], label="Equity Curve", color='blue')
    plt.ylabel("Equity ($)")
    plt.title(f"Equity Curve for {symbol}")
    plt.legend()
    plt.savefig(f"equity_curve_{symbol}.png")
    plt.show()

# Function to plot drawdown curve
def plot_drawdown(stats, symbol):
    plt.figure(figsize=(10, 6))
    plt.plot(stats['_drawdown'], label="Drawdown", color='red')
    plt.ylabel("Drawdown (%)")
    plt.title(f"Drawdown Curve for {symbol}")
    plt.legend()
    plt.savefig(f"drawdown_curve_{symbol}.png")
    plt.show()

# Function to plot % return over time
def plot_return(stats, symbol):
    plt.figure(figsize=(10, 6))
    plt.plot(stats['_equity_curve']['ReturnPct'] * 100, label="Return (%)", color='green')
    plt.ylabel("Return (%)")
    plt.title(f"Percentage Return Over Time for {symbol}")
    plt.legend()
    plt.savefig(f"return_curve_{symbol}.png")
    plt.show()

# Function to run the backtest and plot the results
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
    symbols = ['BTCPERP', 'BTCUSDT', 'SOLPERP', 'SOLUSDT', 'ETHUSDT', 'ETHPERP']  # List of symbols to backtest
    timeframe = '15m'
    start_date = '2023-01-01T00:00:00Z'
    end_date = '2024-09-30T00:00:00Z'

    results = []  # List to store results for each symbol

    for symbol in symbols: # Loop through each symbol and return the value into the results list
        df = fetch_data(symbol, timeframe, start_date, end_date)
        
        # Add ATR and Volatility to the dataframe
        df['ATR'] = calculate_true_range(df).rolling(14).mean()
        df['Volatility'] = calculate_volatility(df)
        
        
        # Run the backtest and store the results for each symbol
        result = run_backtest(df, symbol)
        results.append(result)  # Append the result to the list
        
        # Plot ATR and Volatility
        plot_atr_and_volatility(df, symbol)
        '''plot_equity_curve(stats, symbol)
        plot_drawdown(stats, symbol)
        plot_return(stats, symbol)'''

    # Convert results to a DataFrame and display
    results_df = pd.DataFrame(results)
    print(results_df)