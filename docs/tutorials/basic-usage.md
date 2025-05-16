# Basic Usage Tutorial

This tutorial walks you through a complete workflow using Kura to analyze a dataset of conversations. By the end, you'll understand how to load data, run the clustering process, and visualize the results.

## Prerequisites

Before starting, ensure you have:

1. Installed Kura with: `pip install kura`
2. Set up your API keys:
   ```bash
   export GOOGLE_API_KEY=your_google_api_key
   ```

## Step 1: Setup Your Environment

First, let's import the necessary modules and create a Kura instance:

```python
from kura import Kura
from kura.types import Conversation
import asyncio

# Initialize Kura with default settings
kura = Kura(
    max_clusters=10,  # Target number of top-level clusters
    checkpoint_dir="./tutorial_checkpoints",  # Where to save results
    override_checkpoint_dir=True  # Clear existing checkpoints
)
```

## Step 2: Load Sample Data

For this tutorial, we'll use a sample dataset from Hugging Face:

```python
# Load synthetic conversations from Hugging Face
conversations = Conversation.from_hf_dataset(
    "ivanleomk/synthetic-gemini-conversations",
    split="train"
)

print(f"Loaded {len(conversations)} conversations")
```

> **About the dataset**: `ivanleomk/synthetic-gemini-conversations` contains approximately 190 synthetic conversations focused on technical topics like programming, web development (Django, React, Spring Boot), and software engineering challenges. This dataset is structured in a format compatible with Kura's expected schema, containing conversation IDs, timestamps, and properly formatted messages with user/assistant roles. It serves as an excellent example for demonstrating Kura's clustering capabilities.

## Step 3: Examine the Data

Let's look at a sample conversation to understand its structure:

```python
# Examine first conversation
sample = conversations[0]
print(f"ID: {sample.id}, Messages: {len(sample.messages)}")
print(f"First message: {sample.messages[0].role}: {sample.messages[0].content[:50]}...")
```

## Step 4: Run the Clustering Pipeline

Now, let's process the conversations through the complete Kura pipeline:

```python
# Process all conversations
clustered_data = asyncio.run(kura.cluster_conversations(conversations))

print(f"Generated {len(clustered_data)} projected clusters")
```

This will:

1. Summarize each conversation
2. Create vector embeddings
3. Cluster similar conversations
4. Build a hierarchical structure of clusters
5. Project the clusters for visualization
6. Save all results as checkpoints

## Step 5: Visualize in Terminal

Let's first view the clustering results in the terminal:

```python
# Print the hierarchical clustering results
kura.visualise_clusters()
```

This will display something like:

```
╠══ Compare and improve Flutter and React state management
║   ╚══ Improve and compare Flutter and React state management
║       ╠══ Improve React TypeScript application
║       ╚══ Compare and select Flutter state management solutions
╠══ Optimize blog posts for SEO and improved user engagement
...
```

## Step 6: Start the Web Server

For a more interactive experience, let's start the web server:

```python
# Use the CLI from Python (alternatively, run 'kura' in terminal)
import os
import subprocess

os.environ["KURA_CHECKPOINT_DIR"] = "./tutorial_checkpoints"
subprocess.run(["kura"])
```

Then, open your browser to http://localhost:8000 to explore:

- The cluster map visualization
- The hierarchical cluster tree
- Details about each cluster
- Individual conversations within clusters

## Step 7: Analyze the Results

In the web interface:

1. **Cluster Map**: Click on clusters in the 2D map to see related conversations
2. **Cluster Tree**: Navigate the hierarchical structure to understand relationships
3. **Conversation View**: Examine individual conversations within clusters
4. **Metadata**: If available, use metadata filters to explore subsets of clusters

## Complete Code

Here's the complete code for this tutorial:

```python
from kura import Kura
from kura.types import Conversation
import asyncio
import os
import subprocess

# Create and configure Kura instance
kura = Kura(
    max_clusters=10,
    checkpoint_dir="./tutorial_checkpoints",
    override_checkpoint_dir=True
)

# Load sample data
conversations = Conversation.from_hf_dataset(
    "ivanleomk/synthetic-gemini-conversations",
    split="train"
)
print(f"Loaded {len(conversations)} conversations")

# Examine a sample conversation
sample_conversation = conversations[0]
print(f"Conversation ID: {sample_conversation.id}")
print(f"Created at: {sample_conversation.created_at}")
print(f"Number of messages: {len(sample_conversation.messages)}")
print("\nSample messages:")
for i, msg in enumerate(sample_conversation.messages[:3]):
    print(f"{msg.role}: {msg.content[:100]}..." if len(msg.content) > 100 else f"{msg.role}: {msg.content}")

# Process conversations
clustered_data = asyncio.run(kura.cluster_conversations(conversations))
print(f"Generated {len(clustered_data)} projected clusters")

# View results in terminal
kura.visualise_clusters()

# Start web server
print("\nStarting web server. Press Ctrl+C to stop.")
os.environ["KURA_CHECKPOINT_DIR"] = "./tutorial_checkpoints"
subprocess.run(["kura"])
```

## Next Steps

Now that you've completed the basic tutorial, you can:

1. [Try with your own data](../guides/loading-data.md)
2. [Customize the models](../guides/custom-models.md)
3. [Explore advanced usage](advanced-usage.md)
4. [Work with metadata](../guides/metadata.md)
