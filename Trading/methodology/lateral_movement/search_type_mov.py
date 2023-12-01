import pandas as pd
import numpy as np
from Reports.image_builder import CandlestickChartGenerator
class TrendMovementAnalyzer:
    def __init__(self, df):
        self.data = df
        self.image = CandlestickChartGenerator(self.data)


    def is_upward_trend_SMA(self, window=20):
        """
        Identify if moovemnte is upware.
        :param window: SMA period.
        :return: return boolean value if trand is upware.
        """
        if self.data is None:
            raise ValueError("Data not found.")

        # Verify that dataset contain close column
        if 'Close' not in self.data.columns:
            raise ValueError("Close column is not present.")

        # SMA calculation
        self.data['Moving_Average'] = self.data['Close'].rolling(window=window).mean()

        # Verify if movement is upware
        is_trend_up = self.data['Close'] > self.data['Moving_Average']
        if is_trend_up:
            image =self.image.create_chart_with_SMA(max_points=90)

        return is_trend_up, image

    def is_downward_trend_SMA(self, window=20):
        """
        Identify if moovemnte is downware.
        :param window: SMA period.
        :return: return boolean value if trand is upware.
        """
        if self.data is None:
            raise ValueError("Data not found.")

        # Verify that dataset contain close column
        if 'Close' not in self.data.columns:
            raise ValueError("Close column is not present.")

        # SMA calculation
        self.data['Moving_Average'] = self.data['Close'].rolling(window=window).mean()

        # Verify if movement is downware
        is_trend_down = self.data['Close'] < self.data['Moving_Average']
        if is_trend_down:
            image =self.image.create_chart_with_SMA(max_points=90)
        return is_trend_down, image

    def _calculate_RSI(self, window=14):
        """
        Calcola l'indicatore Relative Strength Index (RSI).
        :param window: Numero di periodi da usare per calcolare l'RSI.
        :return: Serie RSI.
        """
        delta = self.data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def is_upward_trend_using_RSI(self, rsi_threshold=50, window=14):
        """
        Identify if moovement is upware  with RSI support.
        :param rsi_threshold: threshold for to verify if trend is up
        :param window: period number for to define RSI.
        :return: Bool, True if trend is up, False otherwise.
        """
        if self.data is None:
            raise ValueError("Data not found.")

        # RSI
        self.data['RSI'] = self._calculate_RSI(window)

        # Verify if movement is upware
        is_trend_up = self.data['RSI'] > rsi_threshold
        if is_trend_up:
            image =self.image.create_chart_with_RSI(max_points=90)

        return is_trend_up, image

    def is_downward_trend_using_RSI(self, rsi_threshold=50, window=14):
        """
        Identify if moovement is downware  with RSI support.
        :param rsi_threshold: threshold for to verify if trend is down
        :param window: period number for to devine RSI.
        :return: Bool, True if trend is down, False otherwise.
        """
        if self.data is None:
            raise ValueError("Data not found.")

        # RSI
        self.data['RSI'] = self._calculate_RSI(window)

        # Verify if movement is downware
        is_trend_down = self.data['RSI'] < rsi_threshold
        if is_trend_down:
            image =self.image.create_chart_with_RSI(max_points=90)

        return is_trend_down, image

    def _calculate_MACD(self, span_short=12, span_long=26, span_signal=9):
        """
        Calculates the Moving Average Convergence Divergence (MACD).
        :param span_short: Span for the short-term EMA.
        :param span_long: Span for the long-term EMA.
        :param span_signal: Span for the signal line.
        """
        self.data['EMA_short'] = self.data['Close'].ewm(span=span_short, adjust=False).mean()
        self.data['EMA_long'] = self.data['Close'].ewm(span=span_long, adjust=False).mean()
        self.data['MACD'] = self.data['EMA_short'] - self.data['EMA_long']
        self.data['Signal_Line'] = self.data['MACD'].ewm(span=span_signal, adjust=False).mean()

    def is_upward_trend_using_MACD(self):
        """
        Determines if there is an upward trend using MACD.
        :return: Bool, True if there is an upward trend, False otherwise.
        """
        if self.data is None:
            raise ValueError("Data not loaded.")

        self._calculate_MACD()

        # Check if MACD is above the signal line
        is_trend_up = self.data['MACD'].iloc[-1] > self.data['Signal_Line'].iloc[-1]
        if is_trend_up:
            image =self.image.create_chart_with_MACD(max_points=90)

        return is_trend_up, image


    def is_downward_trend_using_MACD(self):
        """
        Determines if there is a downward trend using MACD.
        :return: Bool, True if there is a downward trend, False otherwise.
        """
        if self.data is None:
            raise ValueError("Data not loaded.")

        self._calculate_MACD()
        is_trend_down= self.data['MACD'].iloc[-1] < self.data['Signal_Line'].iloc[-1]
        if is_trend_down:
            image =self.image.create_chart_with_MACD(max_points=90)

        return is_trend_down, image

    def is_lateral_movement_bollinger_bands(self, window=20, num_std_dev=2):
        """
        Determines if there is a lateral movement using Bollinger Bands.
        :param window: Number of periods for the moving average.
        :param num_std_dev: Number of standard deviations for the bands.
        :return: Bool, True if there is a lateral movement, False otherwise.
        """
        self.data['SMA'] = self.data['Close'].rolling(window=window).mean()
        self.data['STD_DEV'] = self.data['Close'].rolling(window=window).std()
        
        self.data['Upper_Band'] = self.data['SMA'] + (self.data['STD_DEV'] * num_std_dev)
        self.data['Lower_Band'] = self.data['SMA'] - (self.data['STD_DEV'] * num_std_dev)
    
        band_width = (self.data['Upper_Band'] - self.data['Lower_Band']) / self.data['SMA']
        return band_width.iloc[-1] < some_threshold # Define a threshold for narrow bands

    def is_lateral_movement_ADX(self, window=14):
        """
        Determines if there is a lateral movement using the Average Directional Index (ADX).
        :param window: Number of periods for the ADX calculation.
        :return: Bool, True if there is a lateral movement, False otherwise.
        """
        # Implement the ADX calculation here (it's a bit complex)
        # ...
    
        return self.data['ADX'].iloc[-1] < adx_threshold # Define a low ADX threshold

    def is_lateral_movement_percent(self, last_periods=5, threshold=0.05):
        """
        Determines if there is a lateral movement based on the percentage change.
        :param window: Number of periods for calculating percentage change.
        :param threshold: Threshold for defining a lateral movement.
        :return: Bool, True if there is a lateral movement, False otherwise.
        """
        if self.data is None:
            raise ValueError("Data not found.")

        # Verify that dataset contain close column
        if 'Close' not in self.data.columns:
            raise ValueError("Close column is not present.")

        # Verify variation price
        self.data['Price_Change'] = self.data['Close'].pct_change()

        cum_change = self.data['Price_Change'].rolling(window=last_periods).sum().abs()

        # Verify if movement is lateral
        is_lateral = cum_change < threshold

        return is_lateral

