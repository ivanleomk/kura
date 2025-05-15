# Configuration

This guide explains the various configuration options available in Kura and how to customize them for your specific needs.

## Main Configuration Parameters

When initializing a `Kura` instance, you can configure various aspects of its behavior:

```python
from kura import Kura
from kura.embedding import OpenAIEmbeddingModel
from kura.summarisation import SummaryModel
from kura.dimensionality import HDBUMAP
from kura.cluster import ClusterModel
from kura.meta_cluster import MetaClusterModel

# Initialize with custom configuration
kura = Kura(
    embedding_model=OpenAIEmbeddingModel(),
    summarisation_model=SummaryModel(),
    cluster_model=ClusterModel(),
    meta_cluster_model=MetaClusterModel(),
    dimensionality_reduction=HDBUMAP(),
    max_clusters=10,
    checkpoint_dir="./my_checkpoints",
    override_checkpoint_dir=False,
    disable_checkpoints=False,
)
```

### Key Parameters

| Parameter                  | Type                          | Default                  | Description                                         |
| -------------------------- | ----------------------------- | ------------------------ | --------------------------------------------------- |
| `embedding_model`          | `BaseEmbeddingModel`          | `OpenAIEmbeddingModel()` | Model used to create embeddings from text           |
| `summarisation_model`      | `BaseSummaryModel`            | `SummaryModel()`         | Model used to generate summaries from conversations |
| `cluster_model`            | `BaseClusterModel`            | `ClusterModel()`         | Model used for initial clustering                   |
| `meta_cluster_model`       | `BaseMetaClusterModel`        | `MetaClusterModel()`     | Model used for hierarchical clustering              |
| `dimensionality_reduction` | `BaseDimensionalityReduction` | `HDBUMAP()`              | Method used to reduce dimensions for visualization  |
| `max_clusters`             | `int`                         | `10`                     | Target number of top-level clusters                 |
| `checkpoint_dir`           | `str`                         | `"./checkpoints"`        | Directory to store checkpoint files                 |
| `override_checkpoint_dir`  | `bool`                        | `False`                  | Whether to clear existing checkpoint directory      |
| `disable_checkpoints`      | `bool`                        | `False`                  | Whether to disable checkpoint saving/loading        |

## Checkpoint Files

Kura saves several checkpoint files during processing:

| Checkpoint File        | Description                      |
| ---------------------- | -------------------------------- |
| `conversations.json`   | Raw conversation data            |
| `summaries.jsonl`      | Summarized conversations         |
| `clusters.jsonl`       | Base cluster data                |
| `meta_clusters.jsonl`  | Hierarchical cluster data        |
| `dimensionality.jsonl` | Projected data for visualization |

You can override the checkpoint filenames if needed:

```python
kura = Kura(
    conversation_checkpoint_name="my_conversations.json",
    summary_checkpoint_name="my_summaries.jsonl",
    cluster_checkpoint_name="my_clusters.jsonl",
    meta_cluster_checkpoint_name="my_meta_clusters.jsonl",
    dimensionality_checkpoint_name="my_dimensionality.jsonl",
)
```

## Customizing Components

Each component of the Kura pipeline can be customized:

### Embedding Model

```python
from kura.embedding import OpenAIEmbeddingModel

# Configure OpenAI embedding model
embedding_model = OpenAIEmbeddingModel(
    model="text-embedding-3-large"
)

kura = Kura(embedding_model=embedding_model)
```

### Summarization Model

```python
from kura.summarisation import SummaryModel

# Configure summarization model with custom extractors
summary_model = SummaryModel(
    extractors=[language_extractor, sentiment_extractor],
    # Configure client rate limits
    concurrent_requests={
        "default": 50,
        "openai": 100,
    }
)

kura = Kura(summarisation_model=summary_model)
```

### Clustering Models

```python
from kura.cluster import ClusterModel
from kura.meta_cluster import MetaClusterModel

# Configure clustering models
cluster_model = ClusterModel(min_cluster_size=5)
meta_cluster_model = MetaClusterModel(similarity_threshold=0.85)

kura = Kura(
    cluster_model=cluster_model,
    meta_cluster_model=meta_cluster_model
)
```

### Dimensionality Reduction

```python
from kura.dimensionality import HDBUMAP

# Configure UMAP for dimensionality reduction
dimensionality_model = HDBUMAP(
    n_neighbours=15,
    min_dist=0.1,
    n_components=2
)

kura = Kura(dimensionality_reduction=dimensionality_model)
```

## CLI Configuration

When using the CLI, you can configure the checkpoint directory:

```bash
# Start the web server with a custom checkpoint directory
kura --dir ./my_checkpoints
```

## Next Steps

Now that you understand how to configure Kura, you can:

- [Learn about core concepts](../core-concepts/overview.md)
- [Explore how to customize models](../guides/custom-models.md)
- [See how to work with metadata](../guides/metadata.md)
