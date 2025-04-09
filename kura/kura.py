from kura.dimensionality import HDBUMAP
from kura.types import Conversation, Cluster, ClusterTreeNode
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
from pathlib import Path
from typing import Union
import os
from typing import TypeVar
from pydantic import BaseModel
from kura.types.dimensionality import ProjectedCluster
from kura.types.summarisation import ConversationSummary

T = TypeVar("T", bound=BaseModel)


class Kura:
    def __init__(
        self,
        embedding_model: BaseEmbeddingModel = OpenAIEmbeddingModel(),
        summarisation_model: BaseSummaryModel = SummaryModel(),
        cluster_model: BaseClusterModel = ClusterModel(),
        meta_cluster_model: BaseMetaClusterModel = MetaClusterModel(),
        dimensionality_reduction: BaseDimensionalityReduction = HDBUMAP(),
        max_clusters: int = 10,
        checkpoint_dir: str = "./checkpoints",
        summary_checkpoint_name: str = "summaries.jsonl",
        cluster_checkpoint_name: str = "clusters.jsonl",
        meta_cluster_checkpoint_name: str = "meta_clusters.jsonl",
        dimensionality_checkpoint_name: str = "dimensionality.jsonl",
        disable_checkpoints: bool = False,
    ):
        # Define Models that we're using
        self.embedding_model = embedding_model
        self.embedding_model = embedding_model
        self.summarisation_model = summarisation_model
        self.max_clusters = max_clusters
        self.cluster_model = cluster_model
        self.meta_cluster_model = meta_cluster_model
        self.dimensionality_reduction = dimensionality_reduction

        # Define Checkpoints
        self.checkpoint_dir = os.path.join(checkpoint_dir)
        self.cluster_checkpoint_name = os.path.join(
            self.checkpoint_dir, cluster_checkpoint_name
        )
        self.meta_cluster_checkpoint_name = os.path.join(
            self.checkpoint_dir, meta_cluster_checkpoint_name
        )
        self.dimensionality_checkpoint_name = os.path.join(
            self.checkpoint_dir, dimensionality_checkpoint_name
        )
        self.summary_checkpoint_name = os.path.join(
            self.checkpoint_dir, summary_checkpoint_name
        )
        self.disable_checkpoints = disable_checkpoints

        if not os.path.exists(self.checkpoint_dir) and not self.disable_checkpoints:
            os.makedirs(self.checkpoint_dir)

        if not self.disable_checkpoints:
            print(f"Checkpoint directory: {Path(self.checkpoint_dir)}")

    def load_checkpoint(
        self, checkpoint_path: str, response_model: type[T]
    ) -> Union[list[T], None]:
        if not self.disable_checkpoints:
            if os.path.exists(checkpoint_path):
                print(
                    f"Loading checkpoint from {checkpoint_path} for {response_model.__name__}"
                )
                with open(checkpoint_path, "r") as f:
                    return [response_model.model_validate_json(line) for line in f]
        return None

    def save_checkpoint(self, checkpoint_path: str, data: list[T]) -> None:
        if not self.disable_checkpoints:
            with open(checkpoint_path, "w") as f:
                for item in data:
                    f.write(item.model_dump_json() + "\n")

    async def reduce_clusters(self, clusters: list[Cluster]) -> list[Cluster]:
        checkpoint_items = self.load_checkpoint(
            self.meta_cluster_checkpoint_name, Cluster
        )
        if checkpoint_items:
            return checkpoint_items

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

        self.save_checkpoint(self.meta_cluster_checkpoint_name, clusters)
        return clusters

    async def summarise_conversations(
        self, conversations: list[Conversation]
    ) -> list[ConversationSummary]:
        checkpoint_items = self.load_checkpoint(
            self.summary_checkpoint_name, ConversationSummary
        )
        if checkpoint_items:
            return checkpoint_items

        summaries = await self.summarisation_model.summarise(conversations)
        self.save_checkpoint(self.summary_checkpoint_name, summaries)
        return summaries

    async def generate_base_clusters(self, summaries: list[ConversationSummary]):
        base_cluster_checkpoint_items = self.load_checkpoint(
            self.cluster_checkpoint_name, Cluster
        )
        if base_cluster_checkpoint_items:
            return base_cluster_checkpoint_items

        clusters: list[Cluster] = await self.cluster_model.cluster_summaries(summaries)
        self.save_checkpoint(self.cluster_checkpoint_name, clusters)
        return clusters

    async def reduce_dimensionality(
        self, clusters: list[Cluster]
    ) -> list[ProjectedCluster]:
        checkpoint_items = self.load_checkpoint(
            self.dimensionality_checkpoint_name, ProjectedCluster
        )
        if checkpoint_items:
            return checkpoint_items

        dimensionality_reduced_clusters = (
            await self.dimensionality_reduction.reduce_dimensionality(clusters)
        )

        self.save_checkpoint(
            self.dimensionality_checkpoint_name, dimensionality_reduced_clusters
        )
        return dimensionality_reduced_clusters

    async def cluster_conversations(self, conversations: list[Conversation]):
        summaries = await self.summarise_conversations(conversations)
        clusters: list[Cluster] = await self.generate_base_clusters(summaries)
        processed_clusters: list[Cluster] = await self.reduce_clusters(clusters)
        dimensionality_reduced_clusters = await self.reduce_dimensionality(
            processed_clusters
        )

        return dimensionality_reduced_clusters

    def _build_tree_structure(
        self,
        node: ClusterTreeNode,
        node_id_to_cluster: dict[str, ClusterTreeNode],
        level: int = 0,
        is_last: bool = True,
        prefix: str = "",
    ):
        # Current line prefix
        current_prefix = prefix

        # Add the appropriate connector based on whether this is the last child
        if level > 0:
            if is_last:
                current_prefix += "╚══ "
            else:
                current_prefix += "╠══ "

        # Print the current node
        result = current_prefix + node.name + "\n"

        # Calculate the prefix for children
        child_prefix = prefix
        if level > 0:
            if is_last:
                child_prefix += "    "
            else:
                child_prefix += "║   "

        # Process children
        children = node.children
        for i, child_id in enumerate(children):
            child = node_id_to_cluster[child_id]
            is_last_child = i == len(children) - 1
            result += self._build_tree_structure(
                child, node_id_to_cluster, level + 1, is_last_child, child_prefix
            )

        return result

    def visualise_clusters(self):
        with open(self.meta_cluster_checkpoint_name) as f:
            clusters = [Cluster.model_validate_json(line) for line in f]

        node_id_to_cluster = {}

        for node in clusters:
            node_id_to_cluster[node.id] = ClusterTreeNode(
                id=node.id,
                name=node.name,
                description=node.description,
                count=node.count,  # type: ignore
                children=[],
            )

        for node in clusters:
            if node.parent_id:
                node_id_to_cluster[node.parent_id].children.append(node.id)

        # Find root nodes and build the tree
        tree_output = ""
        root_nodes = [
            node_id_to_cluster[node.id] for node in clusters if not node.parent_id
        ]

        fake_root = ClusterTreeNode(
            id="root",
            name="Clusters",
            description="All clusters",
            count=0,
            children=[node.id for node in root_nodes],
        )

        tree_output += self._build_tree_structure(
            fake_root, node_id_to_cluster, 0, False
        )

        print(tree_output)
