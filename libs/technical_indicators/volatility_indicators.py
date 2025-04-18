import pandas as pd
import numpy as np

class VolatilityIndicators:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def atr(self, period=14):
        high_low = self.df['High'] - self.df['Low']
        high_close = np.abs(self.df['High'] - self.df['Close'].shift())
        low_close = np.abs(self.df['Low'] - self.df['Close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        self.df[f'ATR_{period}'] = tr.rolling(window=period).mean()
        return self

    def bollinger_bands(self, period=20, num_std=2):
        sma = self.df['Close'].rolling(window=period).mean()
        std = self.df['Close'].rolling(window=period).std()
        self.df[f'BB_Middle_{period}'] = sma
        self.df[f'BB_Upper_{period}'] = sma + num_std * std
        self.df[f'BB_Lower_{period}'] = sma - num_std * std
        return self

    def keltner_channel(self, period=20, atr_mult=1.5):
        typical_price = (self.df['High'] + self.df['Low'] + self.df['Close']) / 3
        ema_tp = typical_price.ewm(span=period, adjust=False).mean()
        high_low = self.df['High'] - self.df['Low']
        tr = high_low.rolling(window=period).mean()
        self.df[f'KC_Middle_{period}'] = ema_tp
        self.df[f'KC_Upper_{period}'] = ema_tp + atr_mult * tr
        self.df[f'KC_Lower_{period}'] = ema_tp - atr_mult * tr
        return self

    @property
    def result(self):
        return self.df


# vol = VolatilityIndicators(df)
# df_with_vol = (
#     vol
#     .atr()
#     .bollinger_bands()
#     .keltner_channel()
#     .result
# )

