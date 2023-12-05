import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from Trading.methodology.lateral_movement.search_type_mov import 

class SupportResistanceFinder:
    def __init__(self, data):
        """
        Inizializza la classe con i dati del mercato.
        :param data: DataFrame contenente i prezzi.
        :param window_size: Dimensione della finestra per le Bande di Bollinger.
        :param num_std_dev: Numero di deviazioni standard per le bande.
        """
        self.data = data

    def calculate_trend_lines(self, peak_points):
        """
        Calcola le linee di trend usando la regressione lineare.
        :param peak_points: Punti (picchi) da utilizzare per la regressione.
        :return: Coefficienti della linea di trend (pendenza e intercetta).
        """
        if len(peak_points) < 2:
            return None  # Non abbastanza punti per una linea di trend

        # Esegui la regressione lineare
        x = peak_points.index
        y = peak_points.values
        slope, intercept = np.polyfit(x, y, 1)
        return slope, intercept

    def find_peaks_for_series(self, series, lateral_period):
        """
        Trova i picchi per una serie di dati in un periodo laterale specificato.
        :param series: Serie di dati (prezzo di apertura, massimo, minimo o chiusura).
        :param lateral_period: Intervallo di tempo del periodo laterale.
        """
        # Limita la ricerca dei picchi al periodo laterale
        lateral_series = series[lateral_period]
        peaks, _ = find_peaks(lateral_series)
        return lateral_series.iloc[peaks]

    def find_support_resistance(self):
        """
        Trova i livelli di supporto e resistenza.
        """
        # Trova i picchi per ogni tipo di prezzo
        max_peaks = pd.concat([self.find_peaks_for_series(self.data[col]) for col in ['Open', 'High', 'Low', 'Close']])
        min_peaks = pd.concat([self.find_peaks_for_series(-self.data[col]) for col in ['Open', 'High', 'Low', 'Close']])

        # Calcola i livelli di supporto e resistenza
        resistance_levels = max_peaks.max()
        support_levels = -min_peaks.max()

        return support_levels, resistance_levels
