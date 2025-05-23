from kura.base_classes import BaseDimensionalityReduction, BaseEmbeddingModel
from kura.types import Cluster, ProjectedCluster
from kura.embedding import OpenAIEmbeddingModel
from typing import Union
import numpy as np
import asyncio


class HDBUMAP(BaseDimensionalityReduction):
    @property
    def checkpoint_filename(self) -> str:
        """The filename to use for checkpointing this model's output."""
        return "dimensionality.jsonl"
    
    def __init__(
        self,
        embedding_model: BaseEmbeddingModel = OpenAIEmbeddingModel(),
        n_components: int = 2,
        min_dist: float = 0.1,
        metric: str = "cosine",
        n_neighbors: Union[int, None] = None,
    ):
        self.embedding_model = embedding_model
        self.n_components = n_components
        self.min_dist = min_dist
        self.metric = metric
        self.n_neighbors = n_neighbors

    async def reduce_dimensionality(
        self, clusters: list[Cluster]
    ) -> list[ProjectedCluster]:
        # Embed all clusters
        from umap import UMAP
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
            n_components=self.n_components,
            n_neighbors=self.n_neighbors
            if self.n_neighbors
            else min(15, len(embeddings) - 1),
            min_dist=self.min_dist,
            metric=self.metric,
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
                level=0
                if cluster.parent_id is None
                else 1,  # TODO: Fix this, should reflect the level of the cluster
            )
            res.append(projected)

        return res
