import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy import stats

class ChannelDetector:
    def __init__(self, df, window, backcandles):
        self.df = df
        self.window = window
        self.backcandles = backcandles

    def isPivot(self, candle):
        """
        function that detects if a candle is a pivot/fractal point
        args: candle index, window before and after candle to test if pivot
        returns: 1 if pivot high, 2 if pivot low, 3 if both and 0 default
        """
        if candle - self.window < 0 or candle + self.window >= len(self.df):
            return 0

        pivotHigh = 1
        pivotLow = 2
        for i in range(candle - self.window, candle + self.window + 1):
            if self.df.iloc[candle].Low > self.df.iloc[i].Low:
                pivotLow = 0
            if self.df.iloc[candle].High < self.df.iloc[i].High:
                pivotHigh = 0
        if (pivotHigh and pivotLow):
            return 3
        elif pivotHigh:
            return pivotHigh
        elif pivotLow:
            return pivotLow
        else:
            return 0

    def pointpos(self, x):
        if x['isPivot'] == 2:
            return x['Low'] - 1e-3
        elif x['isPivot'] == 1:
            return x['High'] + 1e-3
        else:
            return np.nan

    def add_pivot_point_pos(self):
        self.df['isPivot'] = self.df.apply(lambda x: self.isPivot(x.name), axis=1)
        self.df['pointpos'] = self.df.apply(lambda row: self.pointpos(row), axis=1)

    def collect_parallel_channel(self,candle,  parallel):
        localdf = self.df[candle-self.backcandles-self.window:candle-self.window]
        localdf['isPivot'] = localdf.apply(lambda x: self.isPivot(x.name), axis=1)
        highs = localdf[localdf['isPivot']==1].High.values[-3:]
        idxhighs = localdf[localdf['isPivot']==1].High.index[-3:]
        lows = localdf[localdf['isPivot']==2].Low.values[-3:]
        idxlows = localdf[localdf['isPivot']==2].Low.index[-3:]
        total_length = len(lows) + len(highs)
        if len(lows)>=2 and len(highs)>=2 and total_length >= 5:
            sl_lows, interc_lows, r_value_l, _, _ = stats.linregress(idxlows,lows)
            sl_highs, interc_highs, r_value_h, _, _ = stats.linregress(idxhighs,highs)

            if not (parallel>0) or abs( (sl_lows-sl_highs)/(sl_highs+sl_lows)/2 ) < parallel:
                 return(sl_lows, interc_lows, sl_highs, interc_highs, r_value_l**2, r_value_h**2)
        return(0,0,0,0,0,0)

    def plot_pivot_parallel_channel(self, candle):
        dfpl = self.df[candle - self.backcandles - self.window - 5:candle + 200]

        fig = go.Figure(data=[go.Candlestick(x=dfpl.index,
                                             open=dfpl['Open'],
                                             high=dfpl['High'],
                                             low=dfpl['Low'],
                                             close=dfpl['Close'])])

        fig.add_scatter(x=dfpl.index, y=dfpl['pointpos'], mode="markers",
                        marker=dict(size=5, color="MediumPurple"),
                        name="pivot")

        sl_lows, interc_lows, sl_highs, interc_highs, r_sq_l, r_sq_h = self.collect_parallel_channel(candle,
                                                                     parallel=0.1)
        print(r_sq_l, r_sq_h)
        if sl_highs and sl_lows:
            x = np.array(range(candle - self.backcandles - self.window, candle - self.window + 1))
            fig.add_trace(go.Scatter(x=x, y=sl_lows * x + interc_lows, mode='lines', name='lower slope'))
            fig.add_trace(go.Scatter(x=x, y=sl_highs * x + interc_highs, mode='lines', name='max slope'))
        # fig.update_layout(xaxis_rangeslider_visible=False)
        fig.show()



