#!/usr/bin/env python3
"""
Example usage of the procedural Kura implementation.

This script demonstrates how to use the core pipeline functions with keyword arguments
and shows the design philosophy for handling different model types.
"""

import asyncio
import logging
from typing import List

# Import the procedural Kura components
from kura.v1 import (
    summarise_conversations,
    generate_base_clusters_from_conversation_summaries,
    reduce_clusters_from_base_clusters,
    reduce_dimensionality_from_clusters,
    CheckpointManager
)

# Import existing Kura models and types
from kura.types import Conversation
from kura.summarisation import SummaryModel
from kura.cluster import ClusterModel
from kura.meta_cluster import MetaClusterModel
from kura.dimensionality import HDBUMAP

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_conversations() -> List[Conversation]:
    """Create some sample conversations for demonstration."""
    conversations = Conversation.from_hf_dataset(
        "ivanleomk/synthetic-gemini-conversations",
        split="train"
    )
    return conversations


async def basic_pipeline_example():
    """Example: Using individual functions step by step with keyword arguments."""
    logger.info("=== Basic Pipeline Example ===")
    
    conversations = create_sample_conversations()
    
    if not conversations:
        logger.info("No sample conversations available - skipping example")
        return
    
    # Set up models
    summary_model = SummaryModel()
    cluster_model = ClusterModel()
    meta_cluster_model = MetaClusterModel()
    dimensionality_model = HDBUMAP()
    
    # Set up checkpointing (optional)
    checkpoint_manager = CheckpointManager("./tutorial_checkpoints", enabled=True)
    
    try:
        # Step 1: Generate summaries (using keyword arguments)
        summaries = await summarise_conversations(
            conversations,
            model=summary_model,
            checkpoint_manager=checkpoint_manager
        )
        
        # Step 2: Generate base clusters
        clusters = await generate_base_clusters_from_conversation_summaries(
            summaries,
            model=cluster_model,
            checkpoint_manager=checkpoint_manager
        )
        
        # Step 3: Reduce clusters hierarchically
        reduced_clusters = await reduce_clusters_from_base_clusters(
            clusters,
            model=meta_cluster_model,
            checkpoint_manager=checkpoint_manager
        )
        
        # Step 4: Project to 2D for visualization
        projected_clusters = await reduce_dimensionality_from_clusters(
            reduced_clusters,
            model=dimensionality_model,
            checkpoint_manager=checkpoint_manager
        )
        
        logger.info(f"Pipeline complete! Final result: {len(projected_clusters)} projected clusters")
        
    except Exception as e:
        logger.error(f"Error in pipeline: {e}")


async def custom_pipeline_example():
    """Example: Custom pipeline - skip meta-clustering, no checkpointing."""
    logger.info("=== Custom Pipeline Example ===")
    
    conversations = create_sample_conversations()
    
    if not conversations:
        logger.info("No sample conversations available - skipping custom example")
        return
    
    # Set up models
    summary_model = SummaryModel()
    cluster_model = ClusterModel()
    dimensionality_model = HDBUMAP()
    
    try:
        # Generate summaries (no checkpointing)
        summaries = await summarise_conversations(
            conversations, 
            model=summary_model,
            checkpoint_manager=None
        )
        
        # Generate base clusters
        clusters = await generate_base_clusters_from_conversation_summaries(
            summaries, 
            model=cluster_model,
            checkpoint_manager=None
        )
        
        # Skip meta-clustering, go straight to dimensionality reduction
        projected = await reduce_dimensionality_from_clusters(
            clusters, 
            model=dimensionality_model,
            checkpoint_manager=None
        )
        
        logger.info(f"Custom pipeline complete (skipped meta-clustering): {len(projected)} projected clusters")
        
    except Exception as e:
        logger.error(f"Error in custom pipeline: {e}")


async def heterogeneous_models_example():
    """Example: Different model types showing polymorphism."""
    logger.info("=== Heterogeneous Models Example ===")
    
    conversations = create_sample_conversations()
    
    if not conversations:
        logger.info("No sample conversations available - skipping heterogeneous example")
        return
    
    # This example shows how different model types can be used
    # with the same function interface
    
    try:
        # Example 1: Default model
        default_model = SummaryModel()
        summaries1 = await summarise_conversations(
            conversations,
            model=default_model,
            checkpoint_manager=None
        )
        logger.info(f"Default model generated {len(summaries1)} summaries")
        
        # Example 2: Custom configuration
        custom_model = SummaryModel()  # In practice, this might be OpenAISummaryModel, VLLMModel, etc.
        summaries2 = await summarise_conversations(
            conversations,
            model=custom_model,
            checkpoint_manager=None
        )
        logger.info(f"Custom model generated {len(summaries2)} summaries")
        
        # The function interface is the same regardless of model implementation
        logger.info("Both models work with the same function interface!")
        
    except Exception as e:
        logger.error(f"Error in heterogeneous models example: {e}")


def checkpoint_configuration_example():
    """Example: Different checkpoint configurations."""
    logger.info("=== Checkpoint Configuration Example ===")
    
    # Pattern 1: Checkpoints enabled
    checkpoint_manager = CheckpointManager("./my_checkpoints", enabled=True)
    logger.info(f"Checkpoint manager created: {checkpoint_manager.checkpoint_dir}")
    logger.info(f"Checkpoints enabled: {checkpoint_manager.enabled}")
    
    # Pattern 2: Checkpoints disabled
    no_checkpoint_manager = CheckpointManager("./temp", enabled=False)
    logger.info(f"Checkpoints disabled: {no_checkpoint_manager.enabled}")
    
    # Pattern 3: No checkpoint manager (pass None to functions)
    logger.info("Can also pass checkpoint_manager=None to disable checkpointing")


def keyword_arguments_example():
    """Example: Demonstrating the importance of keyword arguments."""
    logger.info("=== Keyword Arguments Example ===")
    
    # Show how keyword arguments make the API more explicit and maintainable
    
    conversations = create_sample_conversations()
    if not conversations:
        logger.info("No conversations available for keyword arguments demo")
        return
    
    logger.info("Recommended usage with keyword arguments:")
    logger.info("""
    # Explicit and clear
    summaries = await summarise_conversations(
        conversations,
        model=my_summary_model,
        checkpoint_manager=my_checkpoint_manager
    )
    
    # Easy to read and understand
    clusters = await generate_base_clusters_from_conversation_summaries(
        summaries,
        model=my_cluster_model,
        checkpoint_manager=None  # Disable checkpointing for this step
    )
    """)
    
    logger.info("This is much clearer than positional arguments!")


async def main():
    """Run all examples."""
    logger.info("Procedural Kura Examples")
    logger.info("=" * 60)
    
    # Run examples
    await basic_pipeline_example()
    await custom_pipeline_example()
    await heterogeneous_models_example()
    checkpoint_configuration_example()
    keyword_arguments_example()
    
    logger.info("=" * 60)
    logger.info("Examples complete!")
    logger.info("Note: Most examples were skipped because no sample conversation data was provided.")
    logger.info("In a real scenario, you would load actual Conversation objects.")
    logger.info("")
    logger.info("Key takeaways:")
    logger.info("1. Use keyword arguments for clarity")
    logger.info("2. Functions work with any model that implements the base interface")
    logger.info("3. Checkpoint management is flexible and optional")
    logger.info("4. Easy to compose custom pipelines")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main()) 