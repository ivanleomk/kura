from kura.dimensionality import HDBUMAP
from kura.types import Conversation, Cluster
from kura.embedding import OpenAIEmbeddingModel
from kura.summarisation import SummaryModel
from kura.meta_cluster import MetaClusterModel
from kura.cluster import ClusterModel
from kura.base_classes import (
    BaseEmbeddingModel,
    BaseSummaryModel,
    BaseClusterModel,
    BaseMetaClusterModel,
    BaseDimensionalityReduction,
)
import json
import os


class Kura:
    def __init__(
        self,
        conversations: list[Conversation] = [],
        embedding_model: BaseEmbeddingModel = OpenAIEmbeddingModel(),
        summarisation_model: BaseSummaryModel = SummaryModel(),
        cluster_model: BaseClusterModel = ClusterModel(),
        meta_cluster_model: BaseMetaClusterModel = MetaClusterModel(),
        dimensionality_reduction: BaseDimensionalityReduction = HDBUMAP(),
        max_clusters: int = 10,
        checkpoint_dir: str = "./checkpoints",
        summary_checkpoint_name: str = "summaries.json",
        cluster_checkpoint_name: str = "clusters.json",
        meta_cluster_checkpoint_name: str = "meta_clusters.json",
        dimensionality_checkpoint_name: str = "dimensionality.json",
        disable_checkpoints: bool = False,
    ):
        # TODO: Manage Checkpoints within Kura class itself so we can directly disable checkpointing easily

        self.embedding_model = embedding_model
        self.embedding_model = embedding_model
        self.summarisation_model = summarisation_model
        self.conversations = conversations
        self.max_clusters = max_clusters
        self.cluster_model = cluster_model
        self.meta_cluster_model = meta_cluster_model
        self.dimensionality_reduction = dimensionality_reduction
        self.checkpoint_dir = checkpoint_dir
        self.cluster_checkpoint_name = cluster_checkpoint_name
        self.meta_cluster_checkpoint_name = meta_cluster_checkpoint_name

    async def reduce_clusters(self, clusters: list[Cluster]) -> list[Cluster]:
        if os.path.exists(
            os.path.join(self.checkpoint_dir, self.cluster_checkpoint_name)
        ):
            print(
                f"Loading Meta Cluster Checkpoint from {self.checkpoint_dir}/{self.cluster_checkpoint_name}"
            )
            with open(
                os.path.join(self.checkpoint_dir, self.cluster_checkpoint_name), "r"
            ) as f:
                return [Cluster(**json.loads(line)) for line in f]

        root_clusters = clusters

        print(f"Starting with {len(root_clusters)} clusters")

        while len(root_clusters) > self.max_clusters:
            # We get the updated list of clusters
            new_current_level = await self.meta_cluster_model.reduce_clusters(
                root_clusters
            )

            # These are the new root clusters that we've generated
            root_clusters = [c for c in new_current_level if c.parent_id is None]

            # We then remove outdated versions of clusters
            old_cluster_ids = {rc.id for rc in new_current_level if rc.parent_id}
            clusters = [c for c in clusters if c.id not in old_cluster_ids]

            # We then add the new clusters to the list
            clusters.extend(new_current_level)

            print(f"Reduced to {len(root_clusters)} clusters")

        with open(
            os.path.join(self.checkpoint_dir, self.cluster_checkpoint_name), "w"
        ) as f:
            print(f"Saving {len(clusters)} clusters to checkpoint")
            for c in clusters:
                f.write(c.model_dump_json() + "\n")

        return clusters

    async def cluster_conversations(self):
        summaries = await self.summarisation_model.summarise(self.conversations)
        clusters: list[Cluster] = await self.cluster_model.cluster_summaries(summaries)
        processed_clusters = await self.reduce_clusters(clusters)
        dimensionality_reduced_clusters = (
            await self.dimensionality_reduction.reduce_dimensionality(
                processed_clusters
            )
        )

        return dimensionality_reduced_clusters
