import pandas as pd
import talib

class VolatilityIndicators:
    def __init__(self, df):
        """
        Initialize the VolatilityIndicators class with a DataFrame.
        :param df: DataFrame containing 'High', 'Low', and 'Close' columns.
        """
        self.df = df

    def add_atr(self, timeperiod=14):
        """
        Add Average True Range (ATR) to the DataFrame.
        ATR measures market volatility by decomposing the entire range of an asset for that period.
        :param timeperiod: The number of periods to use for calculating ATR.
        :return: DataFrame with ATR column added.
        """
        self.df['ATR'] = talib.ATR(self.df['High'], self.df['Low'], self.df['Close'], timeperiod=timeperiod)
        return self.df

    def add_natr(self, timeperiod=14):
        """
        Add Normalized Average True Range (NATR) to the DataFrame.
        NATR normalizes the ATR indicator, making it more comparable across different securities.
        :param timeperiod: The number of periods to use for calculating NATR.
        :return: DataFrame with NATR column added.
        """
        self.df['NATR'] = talib.NATR(self.df['High'], self.df['Low'], self.df['Close'], timeperiod=timeperiod)
        return self.df

    def add_trange(self):
        """
        Add True Range (TRANGE) to the DataFrame.
        TRANGE is the greatest of the current high less the current low, the absolute value of the current high less the previous close, and the absolute value of the current low less the previous close.
        :return: DataFrame with TRANGE column added.
        """
        self.df['TRANGE'] = talib.TRANGE(self.df['High'], self.df['Low'], self.df['Close'])
        return self.df