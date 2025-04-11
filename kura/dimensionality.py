from kura.base_classes import BaseDimensionalityReduction, BaseEmbeddingModel
from kura.types import Cluster, ProjectedCluster
from kura.embedding import OpenAIEmbeddingModel
from umap import UMAP
import numpy as np
import asyncio
import os
from numpy.typing import NDArray
from numpy import float64


class HDBUMAP(BaseDimensionalityReduction):
    def __init__(
        self,
        embedding_model: BaseEmbeddingModel = OpenAIEmbeddingModel(),
    ):
        self.embedding_model = embedding_model

    async def reduce_dimensionality(
        self, clusters: list[Cluster]
    ) -> list[ProjectedCluster]:
        # Embed all clusters
        sem = asyncio.Semaphore(50)
        cluster_embeddings = await asyncio.gather(
            *[
                self.embedding_model.embed(
                    f"Name: {c.name}\nDescription: {c.description}", sem
                )
                for c in clusters
            ]
        )

        # Convert embeddings to numpy array
        embeddings = np.array(cluster_embeddings)

        # Project to 2D using UMAP
        umap_reducer = UMAP(
            n_components=2,
            n_neighbors=min(15, len(embeddings) - 1),
            min_dist=0,
            metric="cosine",
        )
        reduced_embeddings = umap_reducer.fit_transform(embeddings)

        # Create projected clusters with 2D coordinates
        res = []
        for i, cluster in enumerate(clusters):
            projected = ProjectedCluster(
                id=cluster.id,
                name=cluster.name,
                description=cluster.description,
                chat_ids=cluster.chat_ids,
                parent_id=cluster.parent_id,
                x_coord=float(reduced_embeddings[i][0]),  # pyright: ignore
                y_coord=float(reduced_embeddings[i][1]),  # pyright: ignore
                level=0 if cluster.parent_id is None else 1,
                metadata=cluster.metadata,
            )
            res.append(projected)

        return res
