import pandas as pd
import numpy as np

class MomentumIndicators:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def rsi(self, period=14):
        delta = self.df['Close'].diff()

        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        self.df[f'RSI_{period}'] = rsi
        return self

    def stochastic(self, k_period=14, d_period=3):
        low_min = self.df['Low'].rolling(window=k_period).min()
        high_max = self.df['High'].rolling(window=k_period).max()

        self.df['%K'] = 100 * (self.df['Close'] - low_min) / (high_max - low_min)
        self.df['%D'] = self.df['%K'].rolling(window=d_period).mean()
        return self

    def cci(self, period=20):
        tp = (self.df['High'] + self.df['Low'] + self.df['Close']) / 3
        sma = tp.rolling(window=period).mean()
        mad = tp.rolling(window=period).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
        self.df[f'CCI_{period}'] = (tp - sma) / (0.015 * mad)
        return self

    def roc(self, period=12):
        self.df[f'ROC_{period}'] = ((self.df['Close'] - self.df['Close'].shift(period)) / self.df['Close'].shift(period)) * 100
        return self

    def williams_r(self, period=14):
        highest_high = self.df['High'].rolling(window=period).max()
        lowest_low = self.df['Low'].rolling(window=period).min()
        self.df[f"WilliamsR_{period}"] = -100 * (highest_high - self.df['Close']) / (highest_high - lowest_low)
        return self

    @property
    def result(self):
        return self.df


#how to use:
# df = pd.read_csv("your_stock_data.csv", parse_dates=["Date"], index_col="Date")
#
# momentum = MomentumIndicators(df)
# df_with_momentum = (
#     momentum
#     .rsi()
#     .stochastic()
#     .cci()
#     .roc()
#     .williams_r()
#     .result
# )