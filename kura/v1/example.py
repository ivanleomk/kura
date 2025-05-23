#!/usr/bin/env python3
"""
Example usage of the procedural Kura implementation.

This script demonstrates different ways to use the new functional API.
"""

import asyncio
from typing import List

# Import the procedural Kura components
from kura.v1.kura import (
    summarise_conversations,
    generate_base_clusters,
    reduce_clusters,
    reduce_dimensionality,
    run_full_pipeline,
    visualize_clusters,
    PipelineModels,
    PipelineConfig,
    CheckpointManager,
    ProceduralKura
)

# Import existing Kura types (these would come from your actual data)
from kura.types import Conversation


def create_sample_conversations() -> List[Conversation]:
    """Create some sample conversations for demonstration."""
    # This is just for example - in practice you'd load real conversation data
    return [
        # You would create actual Conversation objects here
        # For demo purposes, we'll return an empty list
    ]


async def example_functional_approach():
    """Example 1: Using individual functions for maximum flexibility."""
    print("=== Example 1: Functional Approach ===")
    
    conversations = create_sample_conversations()
    
    if not conversations:
        print("No sample conversations available - skipping functional example")
        return
    
    # Set up configuration
    config = PipelineConfig(
        max_clusters=5,
        checkpoint_dir="./example_checkpoints",
        enable_checkpoints=True,
        enable_progress=True
    )
    
    # Set up models (using defaults)
    models = PipelineModels()
    
    # Set up checkpoint manager
    checkpoint_manager = CheckpointManager(
        config.checkpoint_dir, 
        config.enable_checkpoints
    )
    
    try:
        # Run individual steps
        print("Generating summaries...")
        summaries = await summarise_conversations(
            conversations,
            models.summary_model,
            checkpoint_manager
        )
        print(f"Generated {len(summaries)} summaries")
        
        print("Generating base clusters...")
        clusters = await generate_base_clusters(
            summaries,
            models.cluster_model,
            checkpoint_manager
        )
        print(f"Generated {len(clusters)} base clusters")
        
        print("Reducing clusters...")
        reduced_clusters = await reduce_clusters(
            clusters,
            models.meta_cluster_model,
            checkpoint_manager
        )
        print(f"Reduced to {len([c for c in reduced_clusters if c.parent_id is None])} root clusters")
        
        print("Reducing dimensionality...")
        projected_clusters = await reduce_dimensionality(
            reduced_clusters,
            models.dimensionality_model,
            checkpoint_manager
        )
        print(f"Projected {len(projected_clusters)} clusters to 2D")
        
        # Visualize results
        print("Visualizing clusters...")
        visualize_clusters(reduced_clusters, style="basic")
        
    except Exception as e:
        print(f"Error in functional approach: {e}")


async def example_convenience_function():
    """Example 2: Using the convenience function."""
    print("\n=== Example 2: Convenience Function ===")
    
    conversations = create_sample_conversations()
    
    if not conversations:
        print("No sample conversations available - skipping convenience example")
        return
    
    # Simple configuration
    config = PipelineConfig(
        max_clusters=3,
        checkpoint_dir="./simple_example",
        enable_progress=True
    )
    
    # Default models
    models = PipelineModels()
    
    try:
        # Run the complete pipeline in one call
        print("Running full pipeline...")
        result = await run_full_pipeline(conversations, models, config)
        print(f"Pipeline complete! Generated {len(result)} projected clusters")
        
    except Exception as e:
        print(f"Error in convenience function: {e}")


async def example_backward_compatibility():
    """Example 3: Using the backward compatibility wrapper."""
    print("\n=== Example 3: Backward Compatibility ===")
    
    conversations = create_sample_conversations()
    
    if not conversations:
        print("No sample conversations available - skipping compatibility example")
        return
    
    try:
        # Use exactly like the original Kura class
        kura = ProceduralKura(
            max_clusters=4,
            checkpoint_dir="./compat_example",
            disable_progress=False
        )
        
        print("Running pipeline with compatibility wrapper...")
        result = await kura.cluster_conversations(conversations)
        print(f"Compatibility wrapper complete! Generated {len(result)} projected clusters")
        
        # Use original visualization methods
        print("Visualizing with original methods...")
        kura.visualise_clusters()
        
    except Exception as e:
        print(f"Error in backward compatibility: {e}")


async def example_custom_pipeline():
    """Example 4: Custom pipeline for experimentation."""
    print("\n=== Example 4: Custom Pipeline ===")
    
    conversations = create_sample_conversations()
    
    if not conversations:
        print("No sample conversations available - skipping custom example")
        return
    
    try:
        models = PipelineModels()
        checkpoint_manager = CheckpointManager("./custom_experiment", enabled=False)
        
        # Custom pipeline: Skip meta-clustering, go straight to visualization
        print("Running custom pipeline (skip meta-clustering)...")
        
        summaries = await summarise_conversations(
            conversations, 
            models.summary_model, 
            checkpoint_manager
        )
        print(f"Generated {len(summaries)} summaries")
        
        clusters = await generate_base_clusters(
            summaries, 
            models.cluster_model, 
            checkpoint_manager
        )
        print(f"Generated {len(clusters)} base clusters")
        
        # Skip reduce_clusters step and go straight to dimensionality reduction
        projected = await reduce_dimensionality(
            clusters,  # Use base clusters directly
            models.dimensionality_model, 
            checkpoint_manager
        )
        print(f"Projected {len(projected)} clusters (skipped meta-clustering)")
        
    except Exception as e:
        print(f"Error in custom pipeline: {e}")


def example_configuration_patterns():
    """Example 5: Different configuration patterns."""
    print("\n=== Example 5: Configuration Patterns ===")
    
    # Pattern 1: Minimal config
    minimal_config = PipelineConfig()
    print(f"Minimal config: {minimal_config.max_clusters} clusters, checkpoints: {minimal_config.enable_checkpoints}")
    
    # Pattern 2: Research config (no checkpoints, detailed logging)
    research_config = PipelineConfig(
        max_clusters=15,
        enable_checkpoints=False,
        enable_progress=True,
        checkpoint_dir="./research_temp"
    )
    print(f"Research config: {research_config.max_clusters} clusters, checkpoints: {research_config.enable_checkpoints}")
    
    # Pattern 3: Production config (with checkpoints, minimal output)
    production_config = PipelineConfig(
        max_clusters=8,
        enable_checkpoints=True,
        enable_progress=False,
        checkpoint_dir="./production_checkpoints"
    )
    print(f"Production config: {production_config.max_clusters} clusters, progress: {production_config.enable_progress}")
    
    # Pattern 4: Custom models
    custom_models = PipelineModels(
        # You could provide custom implementations here
        # summary_model=MyCustomSummaryModel(),
        # cluster_model=MyExperimentalClusterModel()
    )
    print(f"Custom models configured")


async def main():
    """Run all examples."""
    print("Procedural Kura Examples")
    print("=" * 50)
    
    # Run examples
    await example_functional_approach()
    await example_convenience_function()
    await example_backward_compatibility()
    await example_custom_pipeline()
    example_configuration_patterns()
    
    print("\n" + "=" * 50)
    print("Examples complete!")
    print("\nNote: Most examples were skipped because no sample conversation data was provided.")
    print("In a real scenario, you would load actual Conversation objects.")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main()) 