# Core Concepts Overview

Kura is built on several key concepts that work together to analyze conversational data. This overview explains the major components and how they interact in the analysis pipeline.

## Architecture

Kura's architecture consists of a pipeline of components that process conversational data through several stages:

![Kura Architecture](../assets/images/kura-architecture.png)

The main components are:

1. **Conversations**: The raw chat data between users and assistants
2. **Summarization**: Converting conversations into concise task descriptions
3. **Embedding**: Representing text as vectors for similarity measurement
4. **Clustering**: Grouping similar summaries into base clusters
5. **Meta-Clustering**: Creating a hierarchical structure of clusters
6. **Dimensionality Reduction**: Projecting high-dimensional embeddings to 2D for visualization

## Processing Pipeline

When you run `kura.cluster_conversations()`, the data flows through the following steps:

1. **Load Conversations**: Raw conversation data is loaded from your specified source
2. **Generate Summaries**: Each conversation is summarized into a task description
3. **Extract Metadata**: Optional metadata is extracted from conversations
4. **Create Embeddings**: Summaries are converted to vector representations
5. **Perform Base Clustering**: Similar summaries are grouped into initial clusters
6. **Apply Meta-Clustering**: Base clusters are iteratively combined into a hierarchical structure
7. **Reduce Dimensions**: High-dimensional embeddings are projected for visualization
8. **Save Checkpoints**: Results from each step are saved as checkpoint files

## Key Classes

Kura is designed with a modular architecture, allowing components to be customized or replaced:

### Main Orchestrator

- **`Kura`** (`kura.py`): The main class that coordinates the entire pipeline and manages checkpoints

### Component Classes

- **`BaseEmbeddingModel`** / **`OpenAIEmbeddingModel`** (`embedding.py`): Convert text to vector representations
- **`BaseSummaryModel`** / **`SummaryModel`** (`summarisation.py`): Generate summaries from conversations
- **`BaseClusterModel`** / **`ClusterModel`** (`cluster.py`): Group similar summaries into clusters
- **`BaseMetaClusterModel`** / **`MetaClusterModel`** (`meta_cluster.py`): Create hierarchical cluster structures
- **`BaseDimensionalityReduction`** / **`HDBUMAP`** (`dimensionality.py`): Project embeddings to 2D space

### Data Models

- **`Conversation`** (`types/conversation.py`): Represents a chat conversation with messages
- **`ConversationSummary`** (`types/summarisation.py`): Contains a summarized conversation
- **`Cluster`** (`types/cluster.py`): Represents a group of similar conversations
- **`ProjectedCluster`** (`types/dimensionality.py`): Represents clusters with 2D coordinates

## Extensibility

Each component has a base class that defines the required interface, allowing you to create custom implementations:

```python
# Example of creating a custom embedding model
from kura.base_classes import BaseEmbeddingModel

class MyCustomEmbeddingModel(BaseEmbeddingModel):
    async def embed(self, texts: list[str]) -> list[list[float]]:
        # Your custom embedding logic here
        ...
```

## Checkpoints

Kura saves intermediate results to checkpoint files, allowing you to:

- Resume processing after interruptions
- Inspect intermediary results
- Share analysis results with others
- Visualize results without reprocessing

## Next Steps

To understand each component in more detail, explore the following pages:

- [Conversations](conversations.md)
- [Summarization](summarization.md)
- [Embedding](embedding.md)
- [Clustering](clustering.md)
- [Meta-Clustering](meta-clustering.md)
- [Dimensionality Reduction](dimensionality-reduction.md)