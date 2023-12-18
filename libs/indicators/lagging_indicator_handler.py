import pandas as pd
import numpy as np

class LaggingIndicators:
    def __init__(self, df):
        """
        Initialize the LaggingIndicators class with a DataFrame.
        :param df: DataFrame containing at least a 'Close' column.
        """
        self.df = df

    def add_sma(self, period=20):
        """
        Add Simple Moving Average (SMA) to the DataFrame.
        SMA is the average of the closing prices over a specified number of periods.
        :param period: Number of periods over which to calculate the SMA.
        :return: DataFrame with the SMA column added.
        """
        self.df[f'SMA_{period}'] = self.df['Close'].rolling(window=period).mean()
        return self.df

    def add_ema(self, period=20):
        """
        Add Exponential Moving Average (EMA) to the DataFrame.
        EMA gives more weight to recent prices and reacts more quickly to price changes than SMA.
        :param period: Number of periods over which to calculate the EMA.
        :return: DataFrame with the EMA column added.
        """
        self.df[f'EMA_{period}'] = self.df['Close'].ewm(span=period, adjust=False).mean()
        return self.df

    def add_macd(self, short_period=12, long_period=26, signal=9):
        """
        Add Moving Average Convergence Divergence (MACD) to the DataFrame.
        MACD is calculated as the difference between a short period EMA and a long period EMA.
        A signal line, which is the EMA of the MACD, is also added.
        :param short_period: Number of periods for the short EMA.
        :param long_period: Number of periods for the long EMA.
        :param signal: Number of periods for the signal line.
        :return: DataFrame with MACD and MACD signal columns added.
        """
        self.df['MACD'] = self.df['Close'].ewm(span=short_period, adjust=False).mean() - \
                          self.df['Close'].ewm(span=long_period, adjust=False).mean()
        self.df['MACD_Signal'] = self.df['MACD'].ewm(span=signal, adjust=False).mean()
        return self.df

    def add_bollinger_bands(self, period=20, std_dev=2):
        """
        Add Bollinger Bands to the DataFrame.
        Bollinger Bands consist of an SMA (middle band) and two standard deviation lines (upper and lower bands).
        :param period: Number of periods for calculating SMA and standard deviation.
        :param std_dev: Number of standard deviations for the upper and lower bands.
        :return: DataFrame with Bollinger Bands columns added.
        """
        sma = self.df['Close'].rolling(window=period).mean()
        rstd = self.df['Close'].rolling(window=period).std()
        self.df['Bollinger_High'] = sma + (rstd * std_dev)
        self.df['Bollinger_Low'] = sma - (rstd * std_dev)
        return self.df

    def add_rsi(self, period=14):
        """
        Add Relative Strength Index (RSI) to the DataFrame.
        RSI is a momentum oscillator that measures the speed and change of price movements.
        :param period: Number of periods for calculating RSI.
        :return: DataFrame with the RSI column added.
        """
        delta = self.df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        self.df['RSI'] = 100 - (100 / (1 + rs))
        return self.df

    def add_all_indicators(self):
        """
        Add all lagging indicators to the DataFrame.
        :return: DataFrame with all lagging indicators added.
        """
        self.add_sma()
        self.add_ema()
        self.add_macd()
        self.add_bollinger_bands()
        self.add_rsi()
        return self.df