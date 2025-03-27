import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN


class DBSCANLevels:
    def __init__(self, df: pd.DataFrame, percentage_eps=0.5, min_samples=5):
        """
        Classe per trovare livelli di supporto e resistenza utilizzando DBSCAN.
        :param df: DataFrame con colonne ['Datetime', 'High', 'Low']
        :param eps: Distanza massima tra due punti per considerarli nello stesso cluster.
        :param min_samples: Numero minimo di punti per formare un cluster.
        """
        self.df = df.copy()
        self.df['Datetime'] = pd.to_datetime(self.df['Datetime'])
        self.eps = self.calculate_eps_percentage()
        self.min_samples = min_samples

    def find_levels(self):
        """
        Trova i livelli di supporto e resistenza utilizzando DBSCAN.
        """
        levels = np.concatenate([self.df['High'].values, self.df['Low'].values]).reshape(-1, 1)
        dbscan = DBSCAN(eps=self.eps, min_samples=self.min_samples)
        clusters = dbscan.fit_predict(levels)

        cluster_levels = pd.DataFrame({'Level': levels.flatten(), 'Cluster': clusters})
        cluster_levels = cluster_levels[cluster_levels['Cluster'] != -1]  # Rimuovere outlier
        significant_levels = cluster_levels.groupby('Cluster')['Level'].mean().values

        return significant_levels

    def calculate_eps_percentage(self, percentage=0.2):
        """
        Calcola il valore di eps come una percentuale del prezzo medio.

        :param df: DataFrame contenente i prezzi
        :param percentage: Percentuale da usare per calcolare eps (es. 0.2% → 0.002)
        :return: eps calcolato dinamicamente
        """
        avg_price = self.df['Close'].mean()  # Usa il prezzo medio dell'azione
        self.eps = avg_price * (percentage / 100)  # Converte percentuale in valore assoluto
        return self.eps