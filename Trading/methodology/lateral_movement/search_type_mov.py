import pandas as pd
import numpy as np

class TrendMovementAnalyzer:
    def __init__(self):
        self.data = None

    def load_data(self, file_path):
        # Carica i dati da un file CSV
        self.data = pd.read_csv(file_path)

    def is_upward_trend(self, window=20):
        """
        Identify if moovemnte is upware.
        :param window: SMA period.
        :return: return boolean value if trand is upware.
        """
        if self.data is None:
            raise ValueError("Data not found."))

        # Verify that dataset contain close column
        if 'Close' not in self.data.columns:
            raise ValueError("Close column is not present.")

        # SMA calculation
        self.data['Moving_Average'] = self.data['Close'].rolling(window=window).mean()

        # Verify if movement is upware
        is_trend_up = self.data['Close'] > self.data['Moving_Average']

        return is_trend_up

   def is_downward_trend(self, window=20):
        """
        Identify if moovemnte is upware.
        :param window: SMA period.
        :return: return boolean value if trand is upware.
        """
        if self.data is None:
            raise ValueError("Data not found."))

        # Verify that dataset contain close column
        if 'Close' not in self.data.columns:
            raise ValueError("Close column is not present.")

        # SMA calculation
        self.data['Moving_Average'] = self.data['Close'].rolling(window=window).mean()

        # Verify if movement is upware
        is_trend_down = self.data['Close'] < self.data['Moving_Average']

        return is_trend_down


    def is_lateral_movement(self, last_periods=5, threshold=0.05):
        """
        Identify if we have lateral movement.
        :param last_periods: number of last period checked.
        :param threshold: level of threshold variation .
        :return: Bool, True if moovement is lateral, False otherwise.
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

    
