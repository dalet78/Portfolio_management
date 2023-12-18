import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from libs.detectors.pivot_handler import PivotDetector

class SupportResistanceFinder:
    def __init__(self, data, n_clusters=7, radius=0.5):
        self.data = data
        self.n_clusters = n_clusters
        self.radius = radius

    def find_optimal_clusters(self, data, max_k=10):
        best_score = -1
        best_k = 2

        for k in range(2, max_k + 1):
            kmeans = KMeans(n_clusters=k)
            kmeans.fit(data)
            score = silhouette_score(data, kmeans.labels_)

            if score > best_score:
                best_score = score
                best_k = k

        return best_k

    def find_levels(self, dynamic_cluster=False):
        pivot_detector = PivotDetector(self.data)
        self.data = pivot_detector.add_pivot_column()
        pivot_values = [pivot[1] for pivot in pivot_detector.pivots]
        pivot_array = np.array(pivot_values).reshape(-1, 1)

        if dynamic_cluster:
            num_clusters = self.find_optimal_clusters(pivot_array)
        else:
            num_clusters = self.n_clusters

        kmeans = KMeans(n_clusters=num_clusters)
        kmeans.fit(pivot_array.round(2))
        levels = kmeans.cluster_centers_

        # Convert array of levels to a sorted list
        levels_list = sorted([level[0] for level in levels])

        return levels_list, self.data

# Esempio di utilizzo:
# Supponiamo che 'data' sia un DataFrame pandas con i dati storici del trading
# finder = SupportResistanceFinder(data, n_clusters=7, radius=0.5)
# support_resistance_levels, data = finder.find_levels(dynamic_cluster=True)
