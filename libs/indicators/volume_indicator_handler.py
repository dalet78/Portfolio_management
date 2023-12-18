import pandas as pd
import numpy as np

class VolumeIndicators:
    def __init__(self, df):
        """
        Initialize the VolumeIndicators class with a DataFrame.
        :param df: DataFrame containing 'Close', 'High', 'Low', 'Volume' columns.
        """
        self.df = df

    def add_obv(self):
        """
        Add On-Balance Volume (OBV) to the DataFrame.
        OBV uses volume flow to predict changes in stock price.
        :return: DataFrame with OBV column added.
        """
        self.df['OBV'] = (np.sign(self.df['Close'].diff()) * self.df['Volume']).fillna(0).cumsum()
        return self.df

    def add_vwap(self):
        """
        Add Volume-Weighted Average Price (VWAP) to the DataFrame.
        VWAP is the average price a security has traded at throughout the day, based on volume and price.
        :return: DataFrame with VWAP column added.
        """
        cum_vol = self.df['Volume'].cumsum()
        cum_vol_price = (self.df['Close'] * self.df['Volume']).cumsum()
        self.df['VWAP'] = cum_vol_price / cum_vol
        return self.df

    def add_ad_line(self):
        """
        Add Accumulation/Distribution Line to the DataFrame.
        A/D Line is a volume-based indicator designed to measure the cumulative flow of money into and out of a security.
        :return: DataFrame with A/D Line column added.
        """
        clv = ((self.df['Close'] - self.df['Low']) - (self.df['High'] - self.df['Close'])) / (self.df['High'] - self.df['Low'])
        clv.fillna(0, inplace=True)  # Handle division by zero
        self.df['AD_Line'] = (clv * self.df['Volume']).cumsum()
        return self.df

    def add_chaikin_mf(self, period=20):
        """
        Add Chaikin Money Flow (CMF) to the DataFrame.
        CMF combines price and volume to view the buying and selling pressure.
        :param period: Number of periods for calculating CMF.
        :return: DataFrame with CMF column added.
        """
        clv = ((self.df['Close'] - self.df['Low']) - (self.df['High'] - self.df['Close'])) / (self.df['High'] - self.df['Low'])
        clv.fillna(0, inplace=True)  # Handle division by zero
        vol_clv = clv * self.df['Volume']
        cmf = vol_clv.rolling(window=period).sum() / self.df['Volume'].rolling(window=period).sum()
        self.df['CMF'] = cmf
        return self.df

    def add_volume_oscillator(self, short_period=12, long_period=26):
        """
        Add Volume Oscillator to the DataFrame.
        Volume Oscillator measures the difference between two moving averages of volume.
        :param short_period: Number of periods for the short moving average.
        :param long_period: Number of periods for the long moving average.
        :return: DataFrame with Volume Oscillator column added.
        """
        short_ma = self.df['Volume'].rolling(window=short_period).mean()
        long_ma = self.df['Volume'].rolling(window=long_period).mean()
        self.df['Volume_Oscillator'] = short_ma - long_ma
        return self.df
