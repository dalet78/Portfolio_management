import pandas as pd

class InversionPatterns:
    def __init__(self, data):
        """
        Inizializza con un DataFrame di dati storici.
        :param data: pd.DataFrame con colonne 'Open', 'High', 'Low', 'Close'.
        """
        self.data = data

    def find_double_top(self, min_distance=5, threshold_percentage=3):
        """
        Identifica i pattern di Doppio Massimo.

        :param min_distance: Il numero minimo di giorni tra i due massimi.
        :param threshold_percentage: La massima differenza percentuale ammessa tra i due massimi.
        :return: Una lista di tuple. Ogni tupla contiene gli indici dei due massimi che formano un Doppio Massimo.
        """
        indices = []
        for i in range(1, len(self.data) - min_distance - 1):
            for j in range(i + min_distance, len(self.data) - 1):
                if self.is_valid_double_top(i, j, threshold_percentage):
                    indices.append((i, j))
        return indices

    def is_valid_double_top(self, i, j, threshold_percentage):
        """
        Valuta se i punti i e j formano un valido Doppio Massimo.

        :param i: Indice del primo massimo.
        :param j: Indice del secondo massimo.
        :param threshold_percentage: Differenza percentuale massima consentita tra i due massimi.
        :return: True se è un Doppio Massimo valido, altrimenti False.
        """
        first_high = self.data['High'][i]
        second_high = self.data['High'][j]

        # Controllo che il primo e il secondo massimo siano vicini in termini percentuali
        percentage_difference = abs(first_high - second_high) / first_high * 100
        if percentage_difference > threshold_percentage:
            return False

        # Verifica che non ci siano massimi superiori tra i e j
        for k in range(i + 1, j):
            if self.data['High'][k] > first_high or self.data['High'][k] > second_high:
                return False

        return True


    def find_double_bottom(self, min_distance=5, threshold_percentage=3):
        """
        Identifica i pattern di Doppio Minimo.

        :param min_distance: Il numero minimo di giorni tra i due minimi.
        :param threshold_percentage: La massima differenza percentuale ammessa tra i due minimi.
        :return: Una lista di tuple. Ogni tupla contiene gli indici dei due minimi che formano un Doppio Minimo.
        """
        indices = []
        for i in range(1, len(self.data) - min_distance - 1):
            for j in range(i + min_distance, len(self.data) - 1):
                if self.is_valid_double_bottom(i, j, threshold_percentage):
                    indices.append((i, j))
        return indices

    def is_valid_double_bottom(self, i, j, threshold_percentage):
        """
        Valuta se i punti i e j formano un valido Doppio Minimo.

        :param i: Indice del primo minimo.
        :param j: Indice del secondo minimo.
        :param threshold_percentage: Differenza percentuale massima consentita tra i due minimi.
        :return: True se è un Doppio Minimo valido, altrimenti False.
        """
        first_low = self.data['Low'][i]
        second_low = self.data['Low'][j]

        # Controllo che il primo e il secondo minimo siano vicini in termini percentuali
        percentage_difference = abs(first_low - second_low) / first_low * 100
        if percentage_difference > threshold_percentage:
            return False

        # Verifica che non ci siano minimi inferiori tra i e j
        for k in range(i + 1, j):
            if self.data['Low'][k] < first_low or self.data['Low'][k] < second_low:
                return False

        return True

    # Metodi simili possono essere aggiunti per altri pattern come Testa e Spalle, ecc.

# Esempio d'uso:
# data = pd.read_csv('path_to_your_data.csv')
# pattern_finder = InversionPatterns(data)
# double_tops = pattern_finder.find_double_top()
# double_bottoms = pattern_finder.find_double_bottom()
