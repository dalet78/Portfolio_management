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