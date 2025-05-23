"""
Procedural implementation of the Kura conversation analysis pipeline.

This module provides a functional approach to conversation analysis, breaking down
the pipeline into composable functions that can be used independently or together.

Key benefits over the class-based approach:
- Better composability and flexibility
- Easier testing of individual steps
- Clearer data flow and dependencies
- Better support for functional programming patterns
"""

from dataclasses import dataclass, field
from typing import Optional, Union, TypeVar, List
import os
from pydantic import BaseModel

# Import existing Kura components
from kura.dimensionality import HDBUMAP
from kura.types import Conversation, Cluster
from kura.embedding import OpenAIEmbeddingModel
from kura.summarisation import SummaryModel
from kura.meta_cluster import MetaClusterModel
from kura.cluster import ClusterModel
from kura.visualization import ClusterVisualizer
from kura.base_classes import (
    BaseEmbeddingModel,
    BaseSummaryModel,
    BaseClusterModel,
    BaseMetaClusterModel,
    BaseDimensionalityReduction,
)
from kura.types.dimensionality import ProjectedCluster
from kura.types import ConversationSummary

# Try to import Rich, fall back gracefully if not available
try:
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    Console = None
    RICH_AVAILABLE = False

T = TypeVar("T", bound=BaseModel)


# =============================================================================
# Configuration Objects
# =============================================================================

@dataclass
class PipelineConfig:
    """Configuration for the Kura pipeline.
    
    Attributes:
        max_clusters: Target number of top-level clusters (deprecated, use in MetaClusterModel)
        checkpoint_dir: Directory for saving intermediate results
        conversation_checkpoint_name: Filename for conversations checkpoint
        enable_checkpoints: Whether to enable checkpoint loading/saving
        enable_progress: Whether to enable progress bars
        console: Optional Rich console instance for output
    """
    max_clusters: int = 10  # Deprecated, kept for backward compatibility
    checkpoint_dir: str = "./checkpoints"
    conversation_checkpoint_name: str = "conversations.json"
    enable_checkpoints: bool = True
    enable_progress: bool = True
    console: Optional['Console'] = None
    
    def __post_init__(self):
        """Initialize console if Rich is available and not provided."""
        if self.console is None and RICH_AVAILABLE and self.enable_progress:
            self.console = Console()


@dataclass
class PipelineModels:
    """Container for all models used in the pipeline.
    
    Attributes:
        embedding_model: Model for converting text to vector embeddings
        summary_model: Model for generating summaries from conversations
        cluster_model: Model for initial clustering of summaries
        meta_cluster_model: Model for creating hierarchical clusters
        dimensionality_model: Model for projecting clusters to 2D space
    """
    embedding_model: BaseEmbeddingModel = field(default_factory=OpenAIEmbeddingModel)
    summary_model: BaseSummaryModel = field(default=None)
    cluster_model: BaseClusterModel = field(default=None)
    meta_cluster_model: BaseMetaClusterModel = field(default=None)
    dimensionality_model: BaseDimensionalityReduction = field(default_factory=HDBUMAP)
    
    def __post_init__(self):
        """Initialize default models with appropriate console settings."""
        # Initialize models that weren't provided
        if self.summary_model is None:
            self.summary_model = SummaryModel()
        if self.cluster_model is None:
            self.cluster_model = ClusterModel()
        if self.meta_cluster_model is None:
            self.meta_cluster_model = MetaClusterModel()


# =============================================================================
# Checkpoint Management
# =============================================================================

class CheckpointManager:
    """Handles checkpoint loading and saving for pipeline steps."""
    
    def __init__(self, checkpoint_dir: str, enabled: bool = True):
        """Initialize checkpoint manager.
        
        Args:
            checkpoint_dir: Directory for saving checkpoints
            enabled: Whether checkpointing is enabled
        """
        self.checkpoint_dir = checkpoint_dir
        self.enabled = enabled
        
        if self.enabled:
            self.setup_checkpoint_dir()
    
    def setup_checkpoint_dir(self) -> None:
        """Create checkpoint directory if it doesn't exist."""
        if not os.path.exists(self.checkpoint_dir):
            os.makedirs(self.checkpoint_dir)
    
    def get_checkpoint_path(self, filename: str) -> str:
        """Get full path for a checkpoint file."""
        return os.path.join(self.checkpoint_dir, filename)
    
    def load_checkpoint(self, filename: str, model_class: type[T]) -> Optional[List[T]]:
        """Load data from a checkpoint file if it exists.
        
        Args:
            filename: Name of the checkpoint file
            model_class: Pydantic model class for deserializing the data
            
        Returns:
            List of model instances if checkpoint exists, None otherwise
        """
        if not self.enabled:
            return None
            
        checkpoint_path = self.get_checkpoint_path(filename)
        if os.path.exists(checkpoint_path):
            print(f"Loading checkpoint from {checkpoint_path} for {model_class.__name__}")
            with open(checkpoint_path, "r") as f:
                return [model_class.model_validate_json(line) for line in f]
        return None
    
    def save_checkpoint(self, filename: str, data: List[T]) -> None:
        """Save data to a checkpoint file.
        
        Args:
            filename: Name of the checkpoint file
            data: List of model instances to save
        """
        if not self.enabled:
            return
            
        checkpoint_path = self.get_checkpoint_path(filename)
        with open(checkpoint_path, "w") as f:
            for item in data:
                f.write(item.model_dump_json() + "\n")


# =============================================================================
# Core Pipeline Functions
# =============================================================================

async def summarise_conversations(
    conversations: List[Conversation],
    model: BaseSummaryModel,
    checkpoint_manager: Optional[CheckpointManager] = None
) -> List[ConversationSummary]:
    """Generate summaries for a list of conversations.
    
    This is a pure function that takes conversations and a summary model,
    and returns conversation summaries. Optionally uses checkpointing.
    
    Args:
        conversations: List of conversations to summarize
        model: Model to use for summarization
        checkpoint_manager: Optional checkpoint manager for caching
        
    Returns:
        List of conversation summaries
    """
    # Try to load from checkpoint
    if checkpoint_manager:
        cached = checkpoint_manager.load_checkpoint(
            model.checkpoint_filename, 
            ConversationSummary
        )
        if cached:
            return cached
    
    # Generate summaries
    summaries = await model.summarise(conversations)
    
    # Save to checkpoint
    if checkpoint_manager:
        checkpoint_manager.save_checkpoint(model.checkpoint_filename, summaries)
    
    return summaries


async def generate_base_clusters(
    summaries: List[ConversationSummary],
    model: BaseClusterModel,
    checkpoint_manager: Optional[CheckpointManager] = None
) -> List[Cluster]:
    """Generate base clusters from conversation summaries.
    
    This function groups similar summaries into initial clusters using
    the provided clustering model.
    
    Args:
        summaries: List of conversation summaries to cluster
        model: Model to use for clustering
        checkpoint_manager: Optional checkpoint manager for caching
        
    Returns:
        List of base clusters
    """
    # Try to load from checkpoint
    if checkpoint_manager:
        cached = checkpoint_manager.load_checkpoint(
            model.checkpoint_filename,
            Cluster
        )
        if cached:
            return cached
    
    # Generate clusters
    clusters = await model.cluster_summaries(summaries)
    
    # Save to checkpoint
    if checkpoint_manager:
        checkpoint_manager.save_checkpoint(model.checkpoint_filename, clusters)
    
    return clusters


async def reduce_clusters(
    clusters: List[Cluster],
    model: BaseMetaClusterModel,
    checkpoint_manager: Optional[CheckpointManager] = None
) -> List[Cluster]:
    """Reduce clusters into a hierarchical structure.
    
    Iteratively combines similar clusters until the number of root clusters
    is less than or equal to the model's max_clusters setting.
    
    Args:
        clusters: List of initial clusters to reduce
        model: Meta-clustering model to use for reduction
        checkpoint_manager: Optional checkpoint manager for caching
        
    Returns:
        List of clusters with hierarchical structure
    """
    # Try to load from checkpoint
    if checkpoint_manager:
        cached = checkpoint_manager.load_checkpoint(
            model.checkpoint_filename,
            Cluster
        )
        if cached:
            return cached
    
    # Start with all clusters as potential roots
    all_clusters = clusters.copy()
    root_clusters = clusters.copy()
    
    print(f"Starting with {len(root_clusters)} clusters")
    
    # Iteratively reduce until we have desired number of root clusters
    while len(root_clusters) > model.max_clusters:
        # Get updated clusters from meta-clustering
        new_current_level = await model.reduce_clusters(root_clusters)
        
        # Find new root clusters (those without parents)
        root_clusters = [c for c in new_current_level if c.parent_id is None]
        
        # Remove old clusters that now have parents
        old_cluster_ids = {c.id for c in new_current_level if c.parent_id}
        all_clusters = [c for c in all_clusters if c.id not in old_cluster_ids]
        
        # Add new clusters to the complete list
        all_clusters.extend(new_current_level)
        
        print(f"Reduced to {len(root_clusters)} clusters")
    
    # Save to checkpoint
    if checkpoint_manager:
        checkpoint_manager.save_checkpoint(model.checkpoint_filename, all_clusters)
    
    return all_clusters


async def reduce_dimensionality(
    clusters: List[Cluster],
    model: BaseDimensionalityReduction,
    checkpoint_manager: Optional[CheckpointManager] = None
) -> List[ProjectedCluster]:
    """Reduce dimensions of clusters for visualization.
    
    Projects clusters to 2D space using the provided dimensionality reduction model.
    
    Args:
        clusters: List of clusters to project
        model: Dimensionality reduction model to use
        checkpoint_manager: Optional checkpoint manager for caching
        
    Returns:
        List of projected clusters with 2D coordinates
    """
    # Try to load from checkpoint
    if checkpoint_manager:
        cached = checkpoint_manager.load_checkpoint(
            model.checkpoint_filename,
            ProjectedCluster
        )
        if cached:
            return cached
    
    # Reduce dimensionality
    projected_clusters = await model.reduce_dimensionality(clusters)
    
    # Save to checkpoint
    if checkpoint_manager:
        checkpoint_manager.save_checkpoint(model.checkpoint_filename, projected_clusters)
    
    return projected_clusters


# =============================================================================
# Convenience Functions
# =============================================================================

async def run_full_pipeline(
    conversations: List[Conversation],
    models: Optional[PipelineModels] = None,
    config: Optional[PipelineConfig] = None
) -> List[ProjectedCluster]:
    """Run the complete Kura pipeline on a list of conversations.
    
    This convenience function orchestrates the entire pipeline:
    1. Summarize conversations
    2. Generate base clusters
    3. Create hierarchical meta-clusters
    4. Project clusters to 2D for visualization
    
    Args:
        conversations: List of conversations to process
        models: Models to use for each step (uses defaults if not provided)
        config: Configuration for the pipeline (uses defaults if not provided)
        
    Returns:
        List of projected clusters with 2D coordinates
    """
    # Use defaults if not provided
    if models is None:
        models = PipelineModels()
    if config is None:
        config = PipelineConfig()
    
    # Set up checkpoint manager
    checkpoint_manager = None
    if config.enable_checkpoints:
        checkpoint_manager = CheckpointManager(config.checkpoint_dir, enabled=True)
        
        # Save original conversations
        if checkpoint_manager.enabled:
            conversation_path = checkpoint_manager.get_checkpoint_path(
                config.conversation_checkpoint_name
            )
            Conversation.generate_conversation_dump(conversations, conversation_path)
    
    # Run pipeline steps
    summaries = await summarise_conversations(
        conversations, models.summary_model, checkpoint_manager
    )
    
    clusters = await generate_base_clusters(
        summaries, models.cluster_model, checkpoint_manager
    )
    
    processed_clusters = await reduce_clusters(
        clusters, models.meta_cluster_model, checkpoint_manager
    )
    
    projected_clusters = await reduce_dimensionality(
        processed_clusters, models.dimensionality_model, checkpoint_manager
    )
    
    return projected_clusters


# =============================================================================
# Visualization Functions
# =============================================================================

def visualize_clusters(
    clusters: List[Cluster],
    style: str = "basic",
    console: Optional['Console'] = None
) -> None:
    """Visualize clusters in the terminal.
    
    Args:
        clusters: List of clusters to visualize
        style: Visualization style ("basic", "enhanced", or "rich")
        console: Optional Rich console for formatted output
    """
    # Create a minimal mock object for the visualizer
    class MockKura:
        def __init__(self, clusters: List[Cluster], console: Optional['Console']):
            self.clusters = clusters
            self.console = console
            
        def load_checkpoint(self, path: str, model_class):
            return self.clusters
            
        @property
        def meta_cluster_checkpoint_path(self):
            return ""
    
    mock_kura = MockKura(clusters, console)
    visualizer = ClusterVisualizer(mock_kura)
    
    if style == "rich" and RICH_AVAILABLE:
        visualizer.visualise_clusters_rich()
    elif style == "enhanced":
        visualizer.visualise_clusters_enhanced()
    else:
        visualizer.visualise_clusters()


# =============================================================================
# Backward Compatibility
# =============================================================================

class ProceduralKura:
    """Compatibility wrapper that provides the old class-based interface.
    
    This allows existing code to work with minimal changes while providing
    access to the new procedural functions underneath.
    """
    
    def __init__(
        self,
        embedding_model: BaseEmbeddingModel = None,
        summarisation_model: BaseSummaryModel = None,
        cluster_model: BaseClusterModel = None,
        meta_cluster_model: BaseMetaClusterModel = None,
        dimensionality_reduction: BaseDimensionalityReduction = None,
        max_clusters: int = 10,
        checkpoint_dir: str = "./checkpoints",
        conversation_checkpoint_name: str = "conversations.json",
        disable_checkpoints: bool = False,
        console: Optional['Console'] = None,
        disable_progress: bool = False,
        **kwargs
    ):
        """Initialize with the same interface as the original Kura class."""
        # Create models container
        self.models = PipelineModels(
            embedding_model=embedding_model or OpenAIEmbeddingModel(),
            summary_model=summarisation_model,
            cluster_model=cluster_model,
            meta_cluster_model=meta_cluster_model,
            dimensionality_model=dimensionality_reduction or HDBUMAP()
        )
        
        # Create config
        self.config = PipelineConfig(
            max_clusters=max_clusters,
            checkpoint_dir=checkpoint_dir,
            conversation_checkpoint_name=conversation_checkpoint_name,
            enable_checkpoints=not disable_checkpoints,
            enable_progress=not disable_progress,
            console=console
        )
        
        # Set up checkpoint manager
        self.checkpoint_manager = CheckpointManager(
            self.config.checkpoint_dir,
            self.config.enable_checkpoints
        ) if self.config.enable_checkpoints else None
    
    async def cluster_conversations(self, conversations: List[Conversation]) -> List[ProjectedCluster]:
        """Run the full pipeline (compatibility method)."""
        return await run_full_pipeline(conversations, self.models, self.config)
    
    async def summarise_conversations(self, conversations: List[Conversation]) -> List[ConversationSummary]:
        """Generate summaries (compatibility method)."""
        return await summarise_conversations(
            conversations, self.models.summary_model, self.checkpoint_manager
        )
    
    async def generate_base_clusters(self, summaries: List[ConversationSummary]) -> List[Cluster]:
        """Generate base clusters (compatibility method)."""
        return await generate_base_clusters(
            summaries, self.models.cluster_model, self.checkpoint_manager
        )
    
    async def reduce_clusters(self, clusters: List[Cluster]) -> List[Cluster]:
        """Reduce clusters (compatibility method)."""
        return await reduce_clusters(
            clusters, self.models.meta_cluster_model, self.checkpoint_manager
        )
    
    async def reduce_dimensionality(self, clusters: List[Cluster]) -> List[ProjectedCluster]:
        """Reduce dimensionality (compatibility method)."""
        return await reduce_dimensionality(
            clusters, self.models.dimensionality_model, self.checkpoint_manager
        )
    
    def visualise_clusters(self):
        """Visualize clusters (compatibility method)."""
        # Load clusters from checkpoint for visualization
        if self.checkpoint_manager:
            clusters = self.checkpoint_manager.load_checkpoint(
                self.models.meta_cluster_model.checkpoint_filename,
                Cluster
            )
            if clusters:
                visualize_clusters(clusters, "basic", self.config.console)
    
    def visualise_clusters_enhanced(self):
        """Visualize clusters with enhanced formatting."""
        if self.checkpoint_manager:
            clusters = self.checkpoint_manager.load_checkpoint(
                self.models.meta_cluster_model.checkpoint_filename,
                Cluster
            )
            if clusters:
                visualize_clusters(clusters, "enhanced", self.config.console)
    
    def visualise_clusters_rich(self):
        """Visualize clusters with Rich formatting."""
        if self.checkpoint_manager:
            clusters = self.checkpoint_manager.load_checkpoint(
                self.models.meta_cluster_model.checkpoint_filename,
                Cluster
            )
            if clusters:
                visualize_clusters(clusters, "rich", self.config.console)


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    # Example of how to use the procedural interface
    
    async def example_usage():
        # Load your conversations
        conversations = []  # Your conversation data here
        
        # Option 1: Use individual functions for maximum flexibility
        models = PipelineModels()
        config = PipelineConfig(max_clusters=5, checkpoint_dir="./my_checkpoints")
        checkpoint_manager = CheckpointManager(config.checkpoint_dir, config.enable_checkpoints)
        
        # Run individual steps
        summaries = await summarise_conversations(conversations, models.summary_model, checkpoint_manager)
        clusters = await generate_base_clusters(summaries, models.cluster_model, checkpoint_manager)
        # ... continue with other steps
        
        # Option 2: Use the convenience function
        projected_clusters = await run_full_pipeline(conversations, models, config)
        
        # Option 3: Use the compatibility wrapper
        kura = ProceduralKura(max_clusters=5, checkpoint_dir="./my_checkpoints")
        result = await kura.cluster_conversations(conversations)
        
        # Visualize results
        visualize_clusters(projected_clusters, style="rich")
    
    # Run example (you would use asyncio.run(example_usage()) in practice) 