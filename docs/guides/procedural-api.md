# Procedural API Guide

This guide provides an in-depth look at Kura's procedural API (v1), which offers a functional programming approach to conversation analysis.

## Overview

The procedural API breaks down the Kura pipeline into composable functions, giving you fine-grained control over each step. This approach is ideal for:

- Custom pipelines with specific requirements
- A/B testing different models
- Debugging and inspecting intermediate results
- Integration with existing systems
- Functional programming workflows

## Core Concepts

### Functions Orchestrate, Models Execute

The procedural API follows a clear separation of concerns:
- **Functions** handle orchestration, data flow, and checkpointing
- **Models** execute the actual ML/AI operations
- All functions accept any model that implements the required interface

### Keyword-Only Arguments

All functions use keyword-only arguments for clarity and maintainability:

```python
# Clear and explicit
summaries = await summarise_conversations(
    conversations,
    model=summary_model,
    checkpoint_manager=checkpoint_mgr
)

# NOT allowed (positional arguments)
summaries = await summarise_conversations(conversations, summary_model)
```

### Polymorphic Model Support

Functions work with any model implementing the base interfaces:

```python
# These all work with the same function
await summarise_conversations(conversations, model=OpenAISummaryModel())
await summarise_conversations(conversations, model=VLLMSummaryModel())
await summarise_conversations(conversations, model=HuggingFaceSummaryModel())
await summarise_conversations(conversations, model=CustomSummaryModel())
```

## Pipeline Functions

### summarise_conversations

Generate summaries from raw conversations:

```python
from kura.v1 import summarise_conversations
from kura.summarisation import SummaryModel

summaries = await summarise_conversations(
    conversations,
    model=SummaryModel(),
    checkpoint_manager=checkpoint_manager
)
```

**Parameters:**
- `conversations`: List of `Conversation` objects
- `model`: Any model implementing `BaseSummaryModel`
- `checkpoint_manager`: Optional checkpoint manager

**Returns:** List of `ConversationSummary` objects

### generate_base_clusters_from_conversation_summaries_from_conversation_summaries

Create initial clusters from summaries:

```python
from kura.v1 import generate_base_clusters_from_conversation_summaries
from kura.cluster import ClusterModel

clusters = await generate_base_clusters_from_conversation_summaries(
    summaries,
    model=ClusterModel(),
    checkpoint_manager=checkpoint_manager
)
```

**Parameters:**
- `summaries`: List of `ConversationSummary` objects
- `model`: Any model implementing `BaseClusterModel`
- `checkpoint_manager`: Optional checkpoint manager

**Returns:** List of `Cluster` objects

### reduce_clusters_from_base_clusters

Build hierarchical cluster structure:

```python
from kura.v1 import reduce_clusters_from_base_clusters
from kura.meta_cluster import MetaClusterModel

reduced = await reduce_clusters_from_base_clusters(
    clusters,
    model=MetaClusterModel(max_clusters=10),
    checkpoint_manager=checkpoint_manager
)
```

**Parameters:**
- `clusters`: List of `Cluster` objects
- `model`: Any model implementing `BaseMetaClusterModel`
- `checkpoint_manager`: Optional checkpoint manager

**Returns:** List of `Cluster` objects with hierarchy

### reduce_dimensionality_from_clusters

Project clusters to 2D for visualization:

```python
from kura.v1 import reduce_dimensionality_from_clusters
from kura.dimensionality import HDBUMAP

projected = await reduce_dimensionality_from_clusters(
    clusters,
    model=HDBUMAP(),
    checkpoint_manager=checkpoint_manager
)
```

**Parameters:**
- `clusters`: List of `Cluster` objects
- `model`: Any model implementing `BaseDimensionalityReduction`
- `checkpoint_manager`: Optional checkpoint manager

**Returns:** List of `ProjectedCluster` objects

## Checkpoint Management

The `CheckpointManager` handles saving and loading intermediate results:

```python
from kura.v1 import CheckpointManager

# Enable checkpointing
checkpoint_mgr = CheckpointManager("./checkpoints", enabled=True)

# Disable checkpointing
no_checkpoint = CheckpointManager("./temp", enabled=False)

# Or pass None to functions
summaries = await summarise_conversations(
    conversations,
    model=model,
    checkpoint_manager=None  # No checkpointing
)
```

## Common Patterns

### Complete Pipeline

```python
async def full_pipeline(conversations):
    # Set up models
    summary_model = SummaryModel()
    cluster_model = ClusterModel()
    meta_cluster_model = MetaClusterModel(max_clusters=10)
    dimensionality_model = HDBUMAP()
    
    # Set up checkpointing
    checkpoint_mgr = CheckpointManager("./analysis", enabled=True)
    
    # Run pipeline
    summaries = await summarise_conversations(
        conversations,
        model=summary_model,
        checkpoint_manager=checkpoint_mgr
    )
    
    clusters = await generate_base_clusters_from_conversation_summaries(
        summaries,
        model=cluster_model,
        checkpoint_manager=checkpoint_mgr
    )
    
    reduced = await reduce_clusters_from_base_clusters(
        clusters,
        model=meta_cluster_model,
        checkpoint_manager=checkpoint_mgr
    )
    
    projected = await reduce_dimensionality_from_clusters(
        reduced,
        model=dimensionality_model,
        checkpoint_manager=checkpoint_mgr
    )
    
    return projected
```

### Custom Pipeline (Skip Steps)

```python
async def clusters_only_pipeline(conversations):
    """Generate clusters without hierarchy or visualization."""
    summary_model = SummaryModel()
    cluster_model = ClusterModel()
    
    summaries = await summarise_conversations(
        conversations,
        model=summary_model,
        checkpoint_manager=None
    )
    
    clusters = await generate_base_clusters_from_conversation_summaries(
        summaries,
        model=cluster_model,
        checkpoint_manager=None
    )
    
    return clusters  # Skip meta-clustering and dimensionality reduction
```

### A/B Testing Models

```python
async def compare_clustering_algorithms(summaries):
    """Compare different clustering approaches."""
    
    # Test HDBSCAN
    hdbscan_clusters = await generate_base_clusters_from_conversation_summaries(
        summaries,
        model=ClusterModel(algorithm="hdbscan"),
        checkpoint_manager=None
    )
    
    # Test KMeans
    kmeans_clusters = await generate_base_clusters_from_conversation_summaries(
        summaries,
        model=ClusterModel(algorithm="kmeans", n_clusters=10),
        checkpoint_manager=None
    )
    
    return {
        "hdbscan": hdbscan_clusters,
        "kmeans": kmeans_clusters
    }
```

### Parallel Processing

```python
async def parallel_summarization(conversation_batches):
    """Process multiple batches in parallel."""
    summary_model = SummaryModel()
    
    # Create tasks for parallel execution
    tasks = [
        summarise_conversations(
            batch,
            model=summary_model,
            checkpoint_manager=None
        )
        for batch in conversation_batches
    ]
    
    # Execute in parallel
    results = await asyncio.gather(*tasks)
    
    # Flatten results
    all_summaries = [s for batch in results for s in batch]
    return all_summaries
```

### Custom Model Integration

```python
class CustomSummaryModel(BaseSummaryModel):
    """Example custom summary model."""
    
    def __init__(self, api_endpoint: str):
        self.api_endpoint = api_endpoint
        self.checkpoint_filename = "custom_summaries.jsonl"
    
    async def summarise(self, conversations: List[Conversation]) -> List[ConversationSummary]:
        # Your custom implementation
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._call_api(session, conv)
                for conv in conversations
            ]
            return await asyncio.gather(*tasks)
    
    async def _call_api(self, session, conversation):
        # API call implementation
        ...

# Use it just like any other model
custom_summaries = await summarise_conversations(
    conversations,
    model=CustomSummaryModel("https://api.example.com"),
    checkpoint_manager=checkpoint_mgr
)
```

## Error Handling

The procedural API maintains the same error handling as the class-based approach:

```python
try:
    summaries = await summarise_conversations(
        conversations,
        model=summary_model,
        checkpoint_manager=checkpoint_mgr
    )
except Exception as e:
    logger.error(f"Failed to generate summaries: {e}")
    # Handle error appropriately
```

## Migration from Class-Based API

### Before (Class-Based)
```python
kura = Kura(
    meta_cluster_model=MetaClusterModel(max_clusters=10),
    checkpoint_dir="./analysis"
)
result = await kura.cluster_conversations(conversations)
```

### After (Procedural)
```python
# Set up models
summary_model = SummaryModel()
cluster_model = ClusterModel()
meta_cluster_model = MetaClusterModel(max_clusters=10)
dimensionality_model = HDBUMAP()
checkpoint_mgr = CheckpointManager("./analysis")

# Run pipeline
summaries = await summarise_conversations(
    conversations,
    model=summary_model,
    checkpoint_manager=checkpoint_mgr
)
# ... continue with other steps
```

## Best Practices

1. **Use keyword arguments**: Always use keyword arguments for clarity
2. **Configure models separately**: Set up models before passing to functions
3. **Handle checkpoints consistently**: Use the same checkpoint manager across steps
4. **Log progress**: Use Python's logging module for tracking
5. **Test individual steps**: The procedural API makes unit testing easier

## Next Steps

- [Create custom models](custom-models.md)
- [Work with metadata](metadata.md)
- [Load different data sources](loading-data.md)
- [Advanced usage patterns](../tutorials/advanced-usage.md)