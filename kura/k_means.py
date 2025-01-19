from kura.base_classes import BaseClusteringMethod
from sklearn.cluster import KMeans
import math
from typing import TypeVar
import numpy as np

T = TypeVar("T")


class KmeansClusteringMethod(BaseClusteringMethod):
    def __init__(self, clusters_per_group: int = 10):
        self.clusters_per_group = clusters_per_group

    def cluster(self, items: list[T]) -> dict[int, list[T]]:
        """
        We perform a clustering here using an embedding defined on each individual item.

        We assume that the item is passed in as a dictionary with

        - its relevant embedding stored in the "embedding" key.
        - the item itself stored in the "item" key.

        {
            "embedding": list[float],
            "item": any,
        }
        """

        embeddings = [item["embedding"] for item in items]  # pyright: ignore
        data: list[T] = [item["item"] for item in items]  # pyright: ignore
        n_clusters = math.ceil(len(data) / self.clusters_per_group)

        X = np.array(embeddings)
        kmeans = KMeans(n_clusters=n_clusters)
        cluster_labels = kmeans.fit_predict(X)

        return {
            i: [data[j] for j in range(len(data)) if cluster_labels[j] == i]
            for i in range(n_clusters)
        }
