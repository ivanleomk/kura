# Quickstart Guide

This guide will help you get started with Kura quickly. We'll cover the basic workflow of analyzing a dataset using Kura's default settings.

## Prerequisites

Before you begin, make sure you have:

1. [Installed Kura](installation.md)
2. Set up your API key for the default Gemini model:
   ```bash
   export GOOGLE_API_KEY=your_api_key_here
   ```

## Basic Workflow

Kura's basic workflow consists of:

1. Loading conversational data
2. Processing the data through summarization, embedding, and clustering
3. Visualizing the results

Let's walk through each step.

## Sample Code

Here's a complete example to get you started with Kura using a sample dataset:

```python
from kura import Kura
from kura.types import Conversation
import asyncio

# Initialize Kura with default settings
kura = Kura()

# Load sample data from Hugging Face
conversations = Conversation.from_hf_dataset(
    "ivanleomk/synthetic-gemini-conversations", 
    split="train"
)

# Process the conversations through the pipeline
asyncio.run(kura.cluster_conversations(conversations))

# Visualize the resulting clusters
kura.visualise_clusters()
```

This will:
1. Initialize Kura with default models
2. Load a sample dataset of synthetic conversations
3. Run the complete analysis pipeline
4. Display the hierarchical clustering results in the terminal

## Using the Web Interface

For a more interactive experience, Kura includes a web interface:

```bash
# After running the clustering process
kura start-app
```

Access the web interface at http://localhost:8000 to explore:
- The cluster map visualization
- Hierarchical cluster tree
- Detailed information for each cluster
- Individual conversations

## Next Steps

Now that you've run your first analysis with Kura, you can:

- [Learn about configuration options](configuration.md) to customize Kura
- Explore [core concepts](../core-concepts/overview.md) to understand how Kura works
- Read about [loading different data formats](../guides/loading-data.md)
- Check out the [tutorials](../tutorials/basic-usage.md) for more detailed examples