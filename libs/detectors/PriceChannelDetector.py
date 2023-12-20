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


def check_pivot_trends_with_sl(dataframe):
    """
    Set 'pivot_high_trend' to True for all rows between two increasing pivot highs,
    and 'pivot_low_trend' to True for all rows between two decreasing pivot lows.
    Also, set the stop loss value based on the last pivot.
    
    :param dataframe: Pandas DataFrame with columns 'isPivot', 'Price', 'High', 'Low'.
                      'isPivot' - 2 indicates a pivot high and 1 indicates a pivot low.
    :return: Updated DataFrame with new columns 'pivot_high_trend', 'pivot_low_trend', 'stop_loss'.
    """
    
    # Initialize trend indicators and stop loss
    dataframe['pivot_high_trend'] = False
    dataframe['pivot_low_trend'] = False
    dataframe['stop_loss'] = None
    
    # Calculate pivot high and low trends
    last_pivot_high_idx = None
    last_pivot_low_idx = None
    last_pivot_high_value = None
    last_pivot_low_value = None
    
    for i, row in dataframe.iterrows():
        if row['isPivot'] == 2:  # Pivot High
            if last_pivot_high_value is not None and row['High'] > last_pivot_high_value:
                dataframe.loc[last_pivot_high_idx:i, 'pivot_high_trend'] = True
            last_pivot_high_idx = i
            last_pivot_high_value = row['High']
    
        elif row['isPivot'] == 1:  # Pivot Low
            if last_pivot_low_value is not None and row['Low'] < last_pivot_low_value:
                dataframe.loc[last_pivot_low_idx:i, 'pivot_low_trend'] = True
            last_pivot_low_idx = i
            last_pivot_low_value = row['Low']
    
        # Set stop loss based on the last pivot
        if row['isPivot'] == 2 and last_pivot_low_value is not None:
            dataframe.at[i, 'stop_loss'] = last_pivot_low_value
        elif row['isPivot'] == 1 and last_pivot_high_value is not None:
            dataframe.at[i, 'stop_loss'] = last_pivot_high_value
    
    return dataframe

def check_pivot_trends_with_numbero_and_sl(dataframe, min_consecutive_high_pivots=2, min_consecutive_low_pivots=2):
    """
    Set 'pivot_high_trend' to True for all rows between two increasing pivot highs,
    and 'pivot_low_trend' to True for all rows between two decreasing pivot lows.
    Also, set the stop loss value based on the last pivot.
    
    :param dataframe: Pandas DataFrame with columns 'isPivot', 'Price', 'High', 'Low'.
                      'isPivot' - 2 indicates a pivot high and 1 indicates a pivot low.
    :param min_consecutive_high_pivots: Minimum number of consecutive pivot highs to consider a high trend.
    :param min_consecutive_low_pivots: Minimum number of consecutive pivot lows to consider a low trend.
    :return: Updated DataFrame with new columns 'pivot_high_trend', 'pivot_low_trend', 'stop_loss'.
    """
    
    # Initialize trend indicators and stop loss
    dataframe['pivot_high_trend'] = False
    dataframe['pivot_low_trend'] = False
    dataframe['stop_loss'] = None
    
    # Variables to track consecutive pivot highs and lows
    consecutive_high_pivots = 0
    consecutive_low_pivots = 0
    last_pivot_high_idx = None
    last_pivot_low_idx = None
    last_pivot_high_value = None
    last_pivot_low_value = None
    
    for i, row in dataframe.iterrows():
        if row['isPivot'] == 2:  # Pivot High
            if last_pivot_high_value is None or row['High'] > last_pivot_high_value:
                consecutive_high_pivots += 1
            else:
                consecutive_high_pivots = 1
            
            if consecutive_high_pivots >= min_consecutive_high_pivots:
                dataframe.loc[last_pivot_high_idx:i, 'pivot_high_trend'] = True
            
            last_pivot_high_idx = i
            last_pivot_high_value = row['High']
    
        elif row['isPivot'] == 1:  # Pivot Low
            if last_pivot_low_value is None or row['Low'] < last_pivot_low_value:
                consecutive_low_pivots += 1
            else:
                consecutive_low_pivots = 1

            if consecutive_low_pivots >= min_consecutive_low_pivots:
                dataframe.loc[last_pivot_low_idx:i, 'pivot_low_trend'] = True

            last_pivot_low_idx = i
            last_pivot_low_value = row['Low']
    
        # Set stop loss based on the last pivot
        if row['isPivot'] == 2 and last_pivot_low_value is not None:
            dataframe.at[i, 'stop_loss'] = last_pivot_low_value
        elif row['isPivot'] == 1 and last_pivot_high_value is not None:
            dataframe.at[i, 'stop_loss'] = last_pivot_high_value
    
    return dataframe
    
