"""
Kura V1: Procedural Implementation

A functional approach to conversation analysis that breaks down the pipeline
into composable functions for better flexibility and testability.
"""

from .kura import (
    # Core pipeline functions
    summarise_conversations,
    generate_base_clusters,
    reduce_clusters,
    reduce_dimensionality,
    
    # Convenience functions
    run_full_pipeline,
    visualize_clusters,
    
    # Configuration and models
    PipelineConfig,
    PipelineModels,
    CheckpointManager,
    
    # Backward compatibility
    ProceduralKura,
)

__all__ = [
    # Core functions
    "summarise_conversations",
    "generate_base_clusters", 
    "reduce_clusters",
    "reduce_dimensionality",
    
    # Convenience functions
    "run_full_pipeline",
    "visualize_clusters",
    
    # Configuration
    "PipelineConfig",
    "PipelineModels", 
    "CheckpointManager",
    
    # Compatibility
    "ProceduralKura",
]

__version__ = "1.0.0" 