# Using the CLI

Kura provides a command-line interface (CLI) for easily starting the web visualization server. This guide explains how to use the CLI effectively.

## Available Commands

Currently, Kura's CLI offers the following command:

- `kura start-app`: Start the web server to visualize clustering results

## Command Usage

### Starting the Web Server

To start the web server with default settings:

```bash
kura start-app
```

This will:
- Load data from the default checkpoint directory (`./checkpoints`)
- Start a web server at http://localhost:8000
- Serve the visualization interface

### Custom Checkpoint Directory

You can specify a custom checkpoint directory:

```bash
kura start-app --dir ./my_checkpoints
```

This allows you to:
- Maintain multiple analysis sessions in different directories
- Share results by pointing to specific checkpoint directories
- Analyze different datasets independently

## Understanding the Output

When you run `kura start-app`, you'll see output similar to:

```
🚀 Access website at http://localhost:8000

INFO:     Started server process [30548]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

The web server will continue running until you press Ctrl+C to stop it.

## Web Interface Features

Once the server is running, you can access the web interface at http://localhost:8000, which provides:

1. **Cluster Map**: Interactive 2D visualization of clusters
2. **Cluster Tree**: Hierarchical view of cluster relationships
3. **Cluster Details**: Information about selected clusters
4. **Conversation Browser**: View conversations within clusters
5. **Metadata Filters**: Filter clusters based on metadata

## Behind the Scenes

The CLI is implemented in `kura/cli/cli.py` using the Typer library and serves the visualization interface using FastAPI and Uvicorn. The web interface itself is a React application that loads data from the checkpoint files.

## Creating Checkpoints

Before using the CLI, you need to generate checkpoint files by running the clustering process:

```python
from kura import Kura
from kura.types import Conversation
import asyncio

kura = Kura(checkpoint_dir="./my_checkpoints")
conversations = Conversation.from_hf_dataset("ivanleomk/synthetic-gemini-conversations")
asyncio.run(kura.cluster_conversations(conversations))
```

After running this code, you can use `kura start-app --dir ./my_checkpoints` to visualize the results.

## Next Steps

Now that you understand how to use the CLI, you might want to:

- [Learn about visualizing results](visualization.md) in more detail
- [Explore loading different data formats](loading-data.md)
- [Discover how to customize models](custom-models.md)