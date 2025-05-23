# Kura V1: Procedural Implementation

This directory contains a procedural, functional approach to the Kura conversation analysis pipeline. Instead of using a single orchestrating class, this implementation breaks the pipeline down into composable functions that can be used independently or together.

## Key Benefits

### 🔧 **Better Composability**
- Use individual functions for maximum flexibility
- Mix and match different steps as needed
- Easy to experiment with different models or configurations

### 🧪 **Easier Testing**
- Test individual pipeline steps in isolation
- Mock dependencies more easily
- Clearer dependency injection

### 📊 **Clearer Data Flow**
- Function signatures make inputs/outputs explicit
- No hidden state or side effects
- Better support for functional programming patterns

### ⚡ **More Flexible**
- Skip steps you don't need
- Run steps in different orders
- Easier to parallelize or optimize individual components

## Usage Examples

### 1. Functional Approach (Maximum Flexibility)

```python
import asyncio
from kura.v1.kura import (
    summarise_conversations, 
    generate_base_clusters, 
    reduce_clusters,
    reduce_dimensionality,
    PipelineModels, 
    PipelineConfig, 
    CheckpointManager
)

async def analyze_conversations(conversations):
    # Set up configuration
    config = PipelineConfig(
        max_clusters=5,
        checkpoint_dir="./my_analysis",
        enable_checkpoints=True
    )
    
    # Set up models
    models = PipelineModels()
    
    # Set up checkpointing
    checkpoint_manager = CheckpointManager(config.checkpoint_dir, config.enable_checkpoints)
    
    # Run individual steps
    summaries = await summarise_conversations(
        conversations, 
        models.summary_model, 
        checkpoint_manager
    )
    
    clusters = await generate_base_clusters(
        summaries, 
        models.cluster_model, 
        checkpoint_manager
    )
    
    # Skip meta-clustering if you want
    # reduced = await reduce_clusters(clusters, models.meta_cluster_model, checkpoint_manager)
    
    # Go straight to dimensionality reduction
    projected = await reduce_dimensionality(
        clusters,  # Use base clusters instead of reduced
        models.dimensionality_model, 
        checkpoint_manager
    )
    
    return projected

# Run it
conversations = load_your_conversations()
result = asyncio.run(analyze_conversations(conversations))
```

### 2. Convenience Function (Easy to Use)

```python
from kura.v1.kura import run_full_pipeline, PipelineModels, PipelineConfig

async def simple_analysis(conversations):
    # Configure the pipeline
    config = PipelineConfig(
        max_clusters=8,
        checkpoint_dir="./simple_analysis",
        enable_progress=True
    )
    
    # Use custom models if needed
    models = PipelineModels(
        # Use defaults or customize
        # summary_model=MyCustomSummaryModel(),
        # cluster_model=MyCustomClusterModel()
    )
    
    # Run the complete pipeline
    result = await run_full_pipeline(conversations, models, config)
    return result

conversations = load_your_conversations()
result = asyncio.run(simple_analysis(conversations))
```

### 3. Backward Compatibility (Drop-in Replacement)

```python
from kura.v1.kura import ProceduralKura

# Use exactly like the original Kura class
kura = ProceduralKura(
    max_clusters=5,
    checkpoint_dir="./compat_test",
    disable_progress=False
)

conversations = load_your_conversations()
result = await kura.cluster_conversations(conversations)

# All the original methods work
kura.visualise_clusters_rich()
```

### 4. Custom Pipeline (Research/Experimentation)

```python
async def experimental_pipeline(conversations):
    models = PipelineModels()
    checkpoint_manager = CheckpointManager("./experiment")
    
    # Generate summaries
    summaries = await summarise_conversations(conversations, models.summary_model, checkpoint_manager)
    
    # Try two different clustering approaches
    clusters_v1 = await generate_base_clusters(summaries, models.cluster_model, checkpoint_manager)
    
    # Use a different model for comparison
    alt_cluster_model = MyExperimentalClusterModel()
    clusters_v2 = await generate_base_clusters(summaries, alt_cluster_model, None)  # No checkpointing
    
    # Compare results or combine them somehow
    best_clusters = compare_and_select(clusters_v1, clusters_v2)
    
    # Continue with the rest of the pipeline
    projected = await reduce_dimensionality(best_clusters, models.dimensionality_model, checkpoint_manager)
    
    return projected
```

### 5. Parallel Processing

```python
import asyncio

async def parallel_analysis(conversation_batches):
    """Process multiple conversation batches in parallel."""
    
    models = PipelineModels()
    
    # Process summaries in parallel
    summary_tasks = [
        summarise_conversations(batch, models.summary_model, None)
        for batch in conversation_batches
    ]
    
    all_summaries = await asyncio.gather(*summary_tasks)
    
    # Flatten and continue with rest of pipeline
    flattened_summaries = [s for batch in all_summaries for s in batch]
    
    # Continue with clustering...
    clusters = await generate_base_clusters(flattened_summaries, models.cluster_model, None)
    
    return clusters
```

## Architecture Overview

### Core Functions
- `summarise_conversations()` - Generate summaries from conversations
- `generate_base_clusters()` - Create initial clusters from summaries  
- `reduce_clusters()` - Build hierarchical cluster structure
- `reduce_dimensionality()` - Project clusters to 2D for visualization

### Supporting Classes
- `PipelineConfig` - Configuration object for pipeline settings
- `PipelineModels` - Container for all models used in pipeline
- `CheckpointManager` - Handles checkpoint loading/saving
- `ProceduralKura` - Backward compatibility wrapper

### Utilities
- `run_full_pipeline()` - Convenience function for complete pipeline
- `visualize_clusters()` - Standalone visualization function

## Migration from Class-based Kura

### Simple Migration
Replace:
```python
from kura import Kura
kura = Kura(max_clusters=5)
result = await kura.cluster_conversations(conversations)
```

With:
```python
from kura.v1.kura import ProceduralKura
kura = ProceduralKura(max_clusters=5)
result = await kura.cluster_conversations(conversations)
```

### Advanced Migration (Take Advantage of New Features)
```python
# Old way
kura = Kura(max_clusters=5, checkpoint_dir="./analysis")
result = await kura.cluster_conversations(conversations)

# New way - more explicit and flexible
from kura.v1.kura import run_full_pipeline, PipelineConfig, PipelineModels

config = PipelineConfig(max_clusters=5, checkpoint_dir="./analysis")
models = PipelineModels()
result = await run_full_pipeline(conversations, models, config)
```

## Advantages Over Class-based Approach

1. **Composability**: Mix and match pipeline steps
2. **Testing**: Test individual functions in isolation
3. **Debugging**: Easier to debug specific steps
4. **Experimentation**: Try different models/configurations easily
5. **Performance**: Can optimize or parallelize individual steps
6. **Functional Programming**: Better support for FP patterns
7. **Clarity**: Function signatures make dependencies explicit

## Backward Compatibility

The `ProceduralKura` class provides a drop-in replacement for the original `Kura` class, so existing code should work with minimal changes. However, you'll get the most benefit by migrating to the functional approach over time. 