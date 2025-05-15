# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Python Environment Setup

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package in development mode with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run a specific test file
pytest tests/test_meta_cluster.py

# Run a specific test
pytest tests/test_meta_cluster.py::test_cluster_label_exact_match
```

### Type Checking

```bash
# Run type checking
pyright
```

### Documentation

```bash
# Install documentation dependencies
pip install -e ".[docs]"

# Serve documentation locally
mkdocs serve
```

### UI Development

```bash
# Navigate to UI directory
cd ui

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Lint code
npm run lint
```

### Running the Application

```bash
# Start the Kura web server
kura start-app

# Start with a custom checkpoint directory
kura start-app --dir ./my-checkpoints
```

## Architecture Overview

Kura is a tool for analyzing and visualizing chat data, built on the same ideas as Anthropic's CLIO. It uses machine learning techniques to understand user conversations by clustering them into meaningful groups.

### Core Components

1. **Summarisation Model**: Takes user conversations and summarizes them into task descriptions
2. **Embedding Model**: Converts text into vector representations (embeddings)
3. **Clustering Model**: Groups summaries into clusters based on embeddings
4. **Meta Clustering Model**: Further groups clusters into a hierarchical structure
5. **Dimensionality Reduction**: Reduces high-dimensional embeddings for visualization

### Data Flow

1. Raw conversations are loaded
2. Conversations are summarized
3. Summaries are embedded and clustered
4. Base clusters are reduced to meta-clusters
5. Dimensionality reduction is applied for visualization
6. Results are saved as checkpoints for persistence

### Key Classes

- `Kura`: Main class that orchestrates the entire pipeline
- `BaseEmbeddingModel` / `OpenAIEmbeddingModel`: Handle text embedding
- `BaseSummaryModel` / `SummaryModel`: Summarize conversations
- `BaseClusterModel` / `ClusterModel`: Create initial clusters
- `BaseMetaClusterModel` / `MetaClusterModel`: Reduce clusters into hierarchical groups
- `BaseDimensionalityReduction` / `HDBUMAP`: Reduce dimensions for visualization

### UI Components

The project includes a React/TypeScript frontend for visualizing the clusters, with components for:
- Displaying cluster maps
- Showing cluster details
- Visualizing cluster hierarchies
- Handling conversation uploads and processing

### Extensibility

The system is designed to be modular, allowing custom implementations of:
- Embedding models
- Summarization models
- Clustering algorithms
- Dimensionality reduction techniques

## Working with Metadata

Kura supports two types of metadata for enriching conversation analysis:

### 1. LLM Extractors
Custom metadata can be extracted from conversations using LLM-powered extractors. These functions run on raw conversations to identify properties like:
- Language detection
- Sentiment analysis
- Topic identification
- Custom metrics

Example of creating a custom extractor:
```python
async def language_extractor(
    conversation: Conversation,
    sems: dict[str, asyncio.Semaphore],
    clients: dict[str, instructor.AsyncInstructor],
) -> ExtractedProperty:
    sem = sems.get("default")
    client = clients.get("default")
    
    async with sem:
        resp = await client.chat.completions.create(
            model="gemini-2.0-flash",
            messages=[
                {
                    "role": "system",
                    "content": "Extract the language of this conversation.",
                },
                {
                    "role": "user",
                    "content": "\n".join(
                        [f"{msg.role}: {msg.content}" for msg in conversation.messages]
                    ),
                },
            ],
            response_model=Language,
        )
        return ExtractedProperty(
            name="language_code",
            value=resp.language_code,
        )
```

### 2. Conversation Metadata
Metadata can be directly attached to conversation objects when loading data:
```python
conversations = Conversation.from_hf_dataset(
    "allenai/WildChat-nontoxic",
    metadata_fn=lambda x: {
        "model": x["model"],
        "toxic": x["toxic"],
        "redacted": x["redacted"],
    },
)
```

## Loading Data

Kura supports multiple data sources:

### Claude Conversation History
```python
from kura.types import Conversation
conversations = Conversation.from_claude_conversation_dump("conversations.json")
```

### Hugging Face Datasets
```python
from kura.types import Conversation
conversations = Conversation.from_hf_dataset(
    "ivanleomk/synthetic-gemini-conversations", 
    split="train"
)
```

### Custom Conversations
For custom data formats, create Conversation objects directly:
```python
from kura.types import Conversation, Message
from datetime import datetime
from uuid import uuid4

conversations = [
    Conversation(
        messages=[
            Message(
                created_at=str(datetime.now()),
                role=message["role"],
                content=message["content"],
            )
            for message in raw_messages
        ],
        id=str(uuid4()),
        created_at=datetime.now(),
    )
]
```

## Checkpoints

Kura uses checkpoint files to save state between runs:
- `conversations.json`: Raw conversation data
- `summaries.jsonl`: Summarized conversations
- `clusters.jsonl`: Base cluster data
- `meta_clusters.jsonl`: Hierarchical cluster data
- `dimensionality.jsonl`: Projected cluster data for visualization

Checkpoints are stored in the directory specified by the `checkpoint_dir` parameter (default: `./checkpoints`).

## Visualization

Kura includes visualization tools:

### CLI Visualization
```python
kura.visualise_clusters()
```

### Web Server
```bash
kura start-app
# Access at http://localhost:8000
```

The web interface provides:
- Interactive cluster map
- Cluster hierarchy tree
- Cluster details panel
- Conversation preview
- Metadata filtering