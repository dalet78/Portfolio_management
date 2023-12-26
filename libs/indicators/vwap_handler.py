import pandas as pd
import numpy as np


class VWAPCalculator:
    def __init__(self, data):
        """
        Inizializza il calcolatore VWAP con i dati di trading.
        :param data: DataFrame pandas con colonne 'price' e 'volume'.
        """
        self.data = data

    def calculate_vwap(self):
        """
        Calcola il VWAP sui dati forniti.
        :return: VWAP come un numero float.
        """
        self.data['cumulative_volume'] = self.data['volume'].cumsum()
        self.data['cumulative_volume_price'] = (self.data['price'] * self.data['volume']).cumsum()
        self.data['vwap'] = self.data['cumulative_volume_price'] / self.data['cumulative_volume']
        return self.data['vwap']

    def calculate_standard_deviation(self):
        """
        Calcola la deviazione standard dei prezzi dal VWAP.
        :return: Deviazione standard come un numero float.
        """
        if self.vwap is None:
            self.calculate_vwap()

        self.data['price_deviation'] = (self.data['price'] - self.vwap) ** 2
        variance = self.data['price_deviation'].sum() / len(self.data)
        return np.sqrt(variance)

    def calculate_second_level_deviation(self):
        """
        Calcola una deviazione di secondo livello (varianza dei prezzi dal VWAP).
        :return: Varianza come un numero float.
        """
        if self.vwap is None:
            self.calculate_vwap()

        self.data['price_deviation'] = (self.data['price'] - self.vwap) ** 2
        return self.data['price_deviation'].sum() / len(self.data)

    def add_vwam_all(self):
        self.calculate_vwap()
        self.calculate_standard_deviation()
        self.calculate_second_level_deviation()
        return self.data


import pandas as pd

class TradingVWAP:
    def __init__(self, data):
        """
        Initialize with a dataframe containing at least 'price' and 'volume' columns.
        """
        self.data = data

    def calculate_vwap(self, timeframe):
        """
        Calculate VWAP for a given timeframe.
        """
        df = self.data.copy()
        df['Datetime'] = pd.to_datetime(df['Datetime'])
        df.set_index('Datetime', inplace=True)
        df['Cumulative_Price_Volume'] = (df['Price'] * df['Volume']).cumsum()
        df['Cumulative_Volume'] = df['Volume'].cumsum()
        df['VWAP'] = df['Cumulative_Price_Volume'] / df['Cumulative_Volume']

        if timeframe in ['D', 'W', 'M', 'Q', 'A']:
            vwap = df.resample(timeframe).last()['VWAP']
        else:
            raise ValueError("Unsupported timeframe. Choose 'D', 'W', 'M', 'Q', or 'A'.")
        
        return vwap

    def calculate_std_deviation(self, vwap_series):
        """
        Calculate the standard deviation for a given VWAP series.
        """
        return vwap_series.std()

    def get_last_values(self, series, n):
        """
        Get the last 'n' values from a series.
        """
        return series[-n:]

    def build_tuples(self):
        """
        Build tuples of the last 3 values for 'W', 'M', 'Q', 'A' and last 5 for 'D'.
        """
        tuples_dict = {}
        for timeframe in ['D', 'W', 'M', 'Q', 'A']:
            vwap = self.calculate_vwap(timeframe)
            std_dev = self.calculate_std_deviation(vwap)
            last_values_vwap = self.get_last_values(vwap, 5 if timeframe == 'D' else 3)
            last_values_std_dev = self.get_last_values(std_dev, 5 if timeframe == 'D' else 3)
            tuples_dict[timeframe] = (last_values_vwap, last_values_std_dev)

        return tuples_dict

# Example usage:
data = pd.read_csv('Data/SP500/Daily/AAL_historical_data.csv')  # Ensure this has 'Datetime', 'Price', and 'Volume'
trading_vwap = TradingVWAP(data)
tuples = trading_vwap.build_tuples()
print(tuples)
