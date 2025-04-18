import pandas as pd
import numpy as np

class VolumeIndicators:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def vwap(self):
        typical_price = (self.df['High'] + self.df['Low'] + self.df['Close']) / 3
        cumulative_vol = self.df['Volume'].cumsum()
        cumulative_tp_vol = (typical_price * self.df['Volume']).cumsum()
        self.df['VWAP'] = cumulative_tp_vol / cumulative_vol
        return self

    def obv(self):
        obv = [0]
        for i in range(1, len(self.df)):
            if self.df['Close'].iloc[i] > self.df['Close'].iloc[i - 1]:
                obv.append(obv[-1] + self.df['Volume'].iloc[i])
            elif self.df['Close'].iloc[i] < self.df['Close'].iloc[i - 1]:
                obv.append(obv[-1] - self.df['Volume'].iloc[i])
            else:
                obv.append(obv[-1])
        self.df['OBV'] = obv
        return self

    def mfi(self, period=14):
        typical_price = (self.df['High'] + self.df['Low'] + self.df['Close']) / 3
        money_flow = typical_price * self.df['Volume']
        direction = np.where(typical_price > typical_price.shift(1), 1,
                             np.where(typical_price < typical_price.shift(1), -1, 0))
        positive_flow = money_flow.where(direction == 1, 0).rolling(window=period).sum()
        negative_flow = money_flow.where(direction == -1, 0).rolling(window=period).sum()
        mfi = 100 * (positive_flow / (positive_flow + negative_flow))
        self.df[f'MFI_{period}'] = mfi
        return self

    def volume_oscillator(self, short_period=5, long_period=20):
        short_ma = self.df['Volume'].rolling(window=short_period).mean()
        long_ma = self.df['Volume'].rolling(window=long_period).mean()
        self.df['Volume_Oscillator'] = ((short_ma - long_ma) / long_ma) * 100
        return self

    @property
    def result(self):
        return self.df

# volume = VolumeIndicators(df)
# df_with_volume = (
#     volume
#     .vwap()
#     .obv()
#     .mfi()
#     .volume_oscillator()
#     .result
# )
