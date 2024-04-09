import numpy as np
import yfinance as yf
from sklearn.cluster import KMeans


class SupportResistanceFinder:
    def __init__(self, data, n_clusters=7, radius=0.5):
        self.n_clusters = n_clusters
        self.radius = radius
        self.data = data

    def identify_pivots(self, close_prices, thresholds=(25, 50, 75), days=(5, 5, 3)):
        pivots = []
        for i in range(max(days), len(close_prices) - max(days)):
            # Determinare il numero di giorni da considerare in base al prezzo
            if close_prices.iloc[i] < thresholds[0]:
                day_range = days[0]
            elif close_prices.iloc[i] < thresholds[1]:
                day_range = days[1]
            elif close_prices.iloc[i] < thresholds[2]:
                day_range = days[2]
            else:
                day_range = days[-1]  # Usa 3 giorni per prezzi superiori a 75

            max_range = close_prices[i - day_range:i + day_range + 1]
            min_range = close_prices[i - day_range:i + day_range + 1]

            if close_prices.iloc[i] == max_range.max():
                pivots.append(close_prices.iloc[i])
            elif close_prices.iloc[i] == min_range.min():
                pivots.append(close_prices.iloc[i])

        return pivots

    def find_levels(self):
        close_prices = self.data['Close']
        pivot_points = self.identify_pivots(close_prices)

        # Se non ci sono abbastanza punti di pivot, ritorna un messaggio di errore
        if len(pivot_points) < self.n_clusters:
            return "Non ci sono abbastanza punti di pivot per applicare K-means"

        # Applicazione del K-means ai punti di pivot
        kmeans = KMeans(n_clusters=self.n_clusters)
        kmeans.fit(np.array(pivot_points).reshape(-1, 1))
        levels = kmeans.cluster_centers_

        return np.sort(levels.round(2), axis=0)