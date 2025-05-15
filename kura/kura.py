from kura.dimensionality import HDBUMAP
from kura.types import Conversation, Cluster, ClusterTreeNode
from kura.embedding import OpenAIEmbeddingModel
from kura.summarisation import SummaryModel
from kura.meta_cluster import MetaClusterModel
from kura.cluster import ClusterModel
import shutil
from kura.base_classes import (
    BaseEmbeddingModel,
    BaseSummaryModel,
    BaseClusterModel,
    BaseMetaClusterModel,
    BaseDimensionalityReduction,
)
from typing import Union
import os
from typing import TypeVar
from pydantic import BaseModel
from kura.types.dimensionality import ProjectedCluster
from kura.types.summarisation import ConversationSummary

T = TypeVar("T", bound=BaseModel)


class Kura:
    """Main class for the Kura conversation analysis pipeline.
    
    Kura is a tool for analyzing conversation data using a multi-step process of
    summarization, embedding, clustering, meta-clustering, and visualization.
    This class coordinates the entire pipeline and manages checkpointing.
    
    Attributes:
        embedding_model: Model for converting text to vector embeddings
        summarisation_model: Model for generating summaries from conversations
        cluster_model: Model for initial clustering of summaries
        meta_cluster_model: Model for creating hierarchical clusters
        dimensionality_reduction: Model for projecting clusters to 2D space
        max_clusters: Target number of top-level clusters
        checkpoint_dir: Directory for saving intermediate results
    """
    
    def __init__(
        self,
        embedding_model: BaseEmbeddingModel = OpenAIEmbeddingModel(),
        summarisation_model: BaseSummaryModel = SummaryModel(),
        cluster_model: BaseClusterModel = ClusterModel(),
        meta_cluster_model: BaseMetaClusterModel = MetaClusterModel(),
        dimensionality_reduction: BaseDimensionalityReduction = HDBUMAP(),
        max_clusters: int = 10,
        checkpoint_dir: str = "./checkpoints",
        conversation_checkpoint_name: str = "conversations.json",
        summary_checkpoint_name: str = "summaries.jsonl",
        cluster_checkpoint_name: str = "clusters.jsonl",
        meta_cluster_checkpoint_name: str = "meta_clusters.jsonl",
        dimensionality_checkpoint_name: str = "dimensionality.jsonl",
        disable_checkpoints: bool = False,
        override_checkpoint_dir: bool = False,
    ):
        """Initialize a new Kura instance with custom or default components.
        
        Args:
            embedding_model: Model to convert text to vector embeddings (default: OpenAIEmbeddingModel)
            summarisation_model: Model to generate summaries from conversations (default: SummaryModel)
            cluster_model: Model for initial clustering (default: ClusterModel)
            meta_cluster_model: Model for hierarchical clustering (default: MetaClusterModel)
            dimensionality_reduction: Model for 2D projection (default: HDBUMAP)
            max_clusters: Target number of top-level clusters (default: 10)
            checkpoint_dir: Directory for saving intermediate results (default: "./checkpoints")
            conversation_checkpoint_name: Filename for conversations checkpoint (default: "conversations.json")
            summary_checkpoint_name: Filename for summaries checkpoint (default: "summaries.jsonl")
            cluster_checkpoint_name: Filename for clusters checkpoint (default: "clusters.jsonl")
            meta_cluster_checkpoint_name: Filename for meta-clusters checkpoint (default: "meta_clusters.jsonl")
            dimensionality_checkpoint_name: Filename for dimensionality checkpoint (default: "dimensionality.jsonl")
            disable_checkpoints: Whether to disable checkpoint loading/saving (default: False)
            override_checkpoint_dir: Whether to clear existing checkpoint directory (default: False)
        """
        # Define Models that we're using
        self.embedding_model = embedding_model
        self.summarisation_model = summarisation_model
        self.max_clusters = max_clusters
        self.cluster_model = cluster_model
        self.meta_cluster_model = meta_cluster_model
        self.dimensionality_reduction = dimensionality_reduction

        # Define Checkpoints
        self.checkpoint_dir = os.path.join(checkpoint_dir)
        self.conversation_checkpoint_name = os.path.join(
            self.checkpoint_dir, conversation_checkpoint_name
        )
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
        self.override_checkpoint_dir = override_checkpoint_dir

    def load_checkpoint(
        self, checkpoint_path: str, response_model: type[T]
    ) -> Union[list[T], None]:
        """Load data from a checkpoint file if it exists.
        
        Args:
            checkpoint_path: Path to the checkpoint file
            response_model: Pydantic model class for deserializing the data
            
        Returns:
            List of model instances if checkpoint exists, None otherwise
        """
        if not self.disable_checkpoints:
            if os.path.exists(checkpoint_path):
                print(
                    f"Loading checkpoint from {checkpoint_path} for {response_model.__name__}"
                )
                with open(checkpoint_path, "r") as f:
                    return [response_model.model_validate_json(line) for line in f]
        return None

    def save_checkpoint(self, checkpoint_path: str, data: list[T]) -> None:
        """Save data to a checkpoint file.
        
        Args:
            checkpoint_path: Path to the checkpoint file
            data: List of model instances to save
        """
        if not self.disable_checkpoints:
            with open(checkpoint_path, "w") as f:
                for item in data:
                    f.write(item.model_dump_json() + "\n")

    def setup_checkpoint_dir(self):
        """Set up the checkpoint directory.
        
        Creates the checkpoint directory if it doesn't exist.
        If override_checkpoint_dir is True, removes and recreates the directory.
        """
        if self.disable_checkpoints:
            return

        if not os.path.exists(self.checkpoint_dir):
            os.makedirs(self.checkpoint_dir)

        if self.override_checkpoint_dir:
            # We will just remove all files for now
            shutil.rmtree(self.checkpoint_dir)
            os.makedirs(self.checkpoint_dir)

    async def reduce_clusters(self, clusters: list[Cluster]) -> list[Cluster]:
        """Reduce clusters into a hierarchical structure.
        
        Iteratively combines similar clusters until the number of root clusters
        is less than or equal to max_clusters.
        
        Args:
            clusters: List of initial clusters
            
        Returns:
            List of clusters with hierarchical structure
        """
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
        """Generate summaries for a list of conversations.
        
        Uses the summarisation_model to generate summaries for each conversation.
        Loads from checkpoint if available.
        
        Args:
            conversations: List of conversations to summarize
            
        Returns:
            List of conversation summaries
        """
        checkpoint_items = self.load_checkpoint(
            self.summary_checkpoint_name, ConversationSummary
        )
        if checkpoint_items:
            return checkpoint_items

        summaries = await self.summarisation_model.summarise(conversations)
        self.save_checkpoint(self.summary_checkpoint_name, summaries)
        return summaries

    async def generate_base_clusters(self, summaries: list[ConversationSummary]) -> list[Cluster]:
        """Generate base clusters from summaries.
        
        Uses the cluster_model to group similar summaries into clusters.
        Loads from checkpoint if available.
        
        Args:
            summaries: List of conversation summaries
            
        Returns:
            List of base clusters
        """
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
        """Reduce dimensions of clusters for visualization.
        
        Uses dimensionality_reduction to project clusters to 2D space.
        Loads from checkpoint if available.
        
        Args:
            clusters: List of clusters to project
            
        Returns:
            List of projected clusters with 2D coordinates
        """
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

    async def cluster_conversations(self, conversations: list[Conversation]) -> list[ProjectedCluster]:
        """Run the full clustering pipeline on a list of conversations.
        
        This is the main method that orchestrates the entire Kura pipeline:
        1. Set up checkpoints directory
        2. Save raw conversations
        3. Generate summaries
        4. Create base clusters
        5. Create hierarchical meta-clusters
        6. Project clusters to 2D for visualization
        
        Args:
            conversations: List of conversations to process
            
        Returns:
            List of projected clusters with 2D coordinates
        """
        self.setup_checkpoint_dir()

        # Configure the checkpoint directory
        if not self.disable_checkpoints:
            Conversation.generate_conversation_dump(
                conversations, self.conversation_checkpoint_name
            )

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
        """Build a text representation of the hierarchical cluster tree.
        
        This is a recursive helper method used by visualise_clusters().
        
        Args:
            node: Current tree node
            node_id_to_cluster: Dictionary mapping node IDs to nodes
            level: Current depth in the tree (for indentation)
            is_last: Whether this is the last child of its parent
            prefix: Current line prefix for tree structure
            
        Returns:
            String representation of the tree structure
        """
        # Current line prefix (used for tree visualization symbols)
        current_prefix = prefix

        # Add the appropriate connector based on whether this is the last child
        if level > 0:
            if is_last:
                current_prefix += "╚══ "
            else:
                current_prefix += "╠══ "

        # Print the current node
        result = (
            current_prefix + node.name + " (" + str(node.count) + " conversations)\n"
        )

        # Calculate the prefix for children (continue vertical lines for non-last children)
        child_prefix = prefix
        if level > 0:
            if is_last:
                child_prefix += "    "  # No vertical line needed for last child's children
            else:
                child_prefix += "║   "  # Continue vertical line for non-last child's children

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
        """Print a hierarchical visualization of clusters to the terminal.
        
        This method loads clusters from the meta_cluster_checkpoint file,
        builds a tree representation, and prints it to the console.
        The visualization shows the hierarchical relationship between clusters
        with indentation and tree structure symbols.
        
        Example output:
        ╠══ Compare and improve Flutter and React state management (45 conversations)
        ║   ╚══ Improve and compare Flutter and React state management (32 conversations)
        ║       ╠══ Improve React TypeScript application (15 conversations)
        ║       ╚══ Compare and select Flutter state management solutions (17 conversations)
        ╠══ Optimize blog posts for SEO and improved user engagement (28 conversations)
        """
        with open(self.meta_cluster_checkpoint_name) as f:
            clusters = [Cluster.model_validate_json(line) for line in f]

        node_id_to_cluster = {}

        for node in clusters:
            node_id_to_cluster[node.id] = ClusterTreeNode(
                id=node.id,
                name=node.name,
                description=node.description,
                count=node.count,  # pyright: ignore
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
            count=sum(node.count for node in root_nodes),
            children=[node.id for node in root_nodes],
        )

        tree_output += self._build_tree_structure(
            fake_root, node_id_to_cluster, 0, False
        )

        print(tree_output)
