# Kura Documentation

## What is Kura?

> Kura is kindly sponsored by [Improving RAG](http://improvingrag.com). If you're wondering what goes on behind the scenes of any production RAG application, ImprovingRAG gives you a clear roadmap as to how to achieve it.

Kura makes it easy to make sense of user data using language models like Gemini. By iteratively summarising and clustering conversations, we can understand broad usage patterns, helping us focus on the specific features to prioritise or issues to fix. It's built with the same ideas as Anthropic's [CLIO](https://www.anthropic.com/research/clio) but open-sourced so that you can try it on your own data.

I've written a [walkthrough of the code](https://ivanleo.com/blog/understanding-user-conversations) if you're interested in understanding the high level ideas.

## Quick Start

> Kura requires python 3.9 because of our dependency on UMAP.

```python
from kura import Kura
from kura.types import Conversation
import asyncio

# Initialize Kura
kura = Kura()

# Load sample data
conversations = Conversation.from_hf_dataset(
    "ivanleomk/synthetic-gemini-conversations", 
    split="train"
)

# Process conversations
asyncio.run(kura.cluster_conversations(conversations))

# Visualize the results
kura.visualise_clusters()
```

To explore more features, check out:
- [Installation Guide](getting-started/installation.md)
- [Quickstart Guide](getting-started/quickstart.md)
- [Core Concepts](core-concepts/overview.md)

## Technical Walkthrough

I've also recorded a technical deep dive into what Kura is and the ideas behind it if you'd rather watch than read.

<iframe width="560" height="315" src="https://www.youtube.com/embed/TPOP_jDiSVE?si=uvTond4LUwJGOn4F" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>