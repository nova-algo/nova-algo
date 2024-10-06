import numpy as np
import pandas as pd
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import ccxt
from datetime import datetime, timedelta

class EnhancedALMAStrategy(Strategy):
    exhaustion_swing_length = 40
    smoothing_factor = 5
    threshold_multiplier = 1.5
    atr_length = 14
    risk_per_trade_percent = 10
    alma_offset = 0.85
    alma_sigma = 6
    pyramiding = 5

    def init(self):
        self.alma = self.I(self.alma_calc, self.data.Close, self.exhaustion_swing_length, self.alma_offset, self.alma_sigma)
        
        # Apply rolling mean directly to the output of alma_calc
        self.smoothed_alma = self.I(lambda x: pd.Series(x).rolling(self.smoothing_factor).mean(), self.alma)
        
        self.atr = self.I(lambda x: pd.Series(x).rolling(self.atr_length).mean(), self.data.TR)
        self.dynamic_threshold = self.I(lambda x: pd.Series(x) * self.threshold_multiplier, self.atr)
        
        self.upper_band = self.I(lambda x, y: pd.Series(x) + pd.Series(y).rolling(self.exhaustion_swing_length).std() * 1.5, self.smoothed_alma, self.data.Close)
        self.lower_band = self.I(lambda x, y: pd.Series(x) - pd.Series(y).rolling(self.exhaustion_swing_length).std() * 1.5, self.smoothed_alma, self.data.Close)
        
        self.resistance_level = self.I(self.calculate_resistance, self.data.Close, self.upper_band)
        self.support_level = self.I(self.calculate_support, self.data.Close, self.lower_band)

    def alma_calc(self, price, window, offset, sigma):
        m = np.floor(offset * (window - 1))
        s = window / sigma
        w = np.exp(-((np.arange(window) - m) ** 2) / (2 * s * s))
        w /= w.sum()

        def alma(x):
            return (np.convolve(x, w[::-1], mode='valid'))[0]

        return pd.Series(price).rolling(window).apply(alma, raw=True)

    def calculate_resistance(self, close, upper_band):
        resistance = np.where(crossover(close, upper_band), close, np.nan)
        return pd.Series(resistance).fillna(method='ffill')

    def calculate_support(self, close, lower_band):
        support = np.where(crossover(lower_band, close), close, np.nan)
        return pd.Series(support).fillna(method='ffill')

    def next(self):
        price = self.data.Close[-1]
        
        if len(self.trades) >= self.pyramiding:
            return
        
        position_size = self.position.size
        
        if crossover(self.data.Close, self.smoothed_alma + self.dynamic_threshold):
            if position_size < 1:
                self.position.close()
            self.buy(size=0.1)
        
        elif crossover(self.smoothed_alma - self.dynamic_threshold, self.data.Close):
            if position_size > 1:
                self.position.close()
            self.sell(size=0.1)

    def position_size(self):
        return (self.equity * (self.risk_per_trade_percent / 100)) # / self.atr[-1]
    
def calculate_true_range(df):
    df['Previous Close'] = df['Close'].shift(1)
    df['High-Low'] = df['High'] - df['Low']
    df['High-PrevClose'] = abs(df['High'] - df['Previous Close'])
    df['Low-PrevClose'] = abs(df['Low'] - df['Previous Close'])
    df['TR'] = df[['High-Low', 'High-PrevClose', 'Low-PrevClose']].max(axis=1)
    return df['TR']

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
            print(f"Error fetching data: {e}")
            break
    
    df = pd.DataFrame(all_ohlcv, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
    # print("before datetime\n", df)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
    df = df.set_index('Timestamp')
    df['TR'] = calculate_true_range(df)
    df.index = pd.to_datetime(df.index)
    #print("timestamp df\n", df)
    # df = df[(df.index >= pd.Timestamp(start_date)) & (df.index <= pd.Timestamp(end_date))]
    #print('start to end time\n', df)
    return df

def run_backtest(df):
    bt = Backtest(df, EnhancedALMAStrategy, cash=100000, commission=.002)
    stats = bt.run()
    print(stats)
    #bt.plot()

if __name__ == "__main__":
    symbol = 'SOLPERP'
    timeframe = '15m'
    start_date = '2023-01-01T00:00:00Z'
    end_date = '2024-09-30T00:00:00Z'
    
    df = fetch_data(symbol, timeframe, start_date, end_date)
    run_backtest(df)