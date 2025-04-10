# Index

## What is Kura?

> Kura is kindly sponsored by [Improving RAG](http://improvingrag.com). If you're wondering what goes on behind the scenes of any production RAG application, ImprovingRAG gives you a clear roadmap as to how to achieve it.

Kura makes it easy to make sense of user data using language models like Gemini. By iteratively summarising and clustering conversations, we can understand broad usage patterns, helping us focus on the specific features to prioritise or issues to fix. It's built with the same ideas as Anthropic's [CLIO](https://www.anthropic.com/research/clio) but open-sourced so that you can try it on your own data.

I've written a [walkthrough of the code](https://ivanleo.com/blog/understanding-user-conversations) if you're interested in understanding the high level ideas.

## Instructions

> Kura requires python 3.9 because of our dependency on UMAP.

Get started by installing Kura using `pip`. We recommend using `uv` to do so.

```
uv pip install kura datasets
```

To test Kura out, we've provided a sample dataset of [~190+ synthetically generated conversations](https://huggingface.co/datasets/ivanleomk/synthetic-gemini-conversations) on Hugging Face that we used to validate Kura's clustering ability.

```py
from kura import Kura
from kura.types import Conversation
import asyncio

kura = Kura()
conversations = Conversation.from_hf_dataset(
    "ivanleomk/synthetic-gemini-conversations", split="train"
)
asyncio.run(kura.cluster_conversations(conversations))

kura.visualise_clusters()
```

This will print out a list of clusters as seen below that we've identified

```bash
╠══ Compare and improve Flutter and React state management
║   ╚══ Improve and compare Flutter and React state management
║       ╠══ Improve React TypeScript application
║       ╚══ Compare and select Flutter state management solutions
╠══ Optimize blog posts for SEO and improved user engagement
.....
```

## Loading Custom Datasets

We support a large variety of different dataset types with support for HuggingFace datasets and Claude Conversation History

### Claude Conversation History

> If you're using the Claude app, you can export your conversation history [here](https://support.anthropic.com/en/articles/9450526-how-can-i-export-my-claude-ai-data) and use the `Conversation.from_claude_conversation_dump` method to load them into Kura.

We also support Claude conversations out of the box, which you can import as seen below.

```python
from kura import Kura
from kura.types import Conversation
import asyncio

kura = Kura(max_clusters=10) # Set Max Cluster Size ( We will keep recursively combining until we reach this max_clusters size )

conversations = Conversation.from_claude_conversation_dump("conversations.json")

asyncio.run(kura.cluster_conversations(conversations))

kura.visualise_clusters()

```

### Hugging Face Datasets

We also provide a simple method to load in dataset entries from huggingface from our `Conversation` class as seen below.

By default we expect the following columns

- `chat_id` : This identifies a unique conversation by its id
- `created_at` : This is mostly just used for timeseries analysis
- `content` : This expects messages that we'll then concatenate and summarise down the line.

If your Hugging Face dataset does not have these fields, we provide the mappings of `chat_id_fn`, `created_at_fn` and `messages_fn` as ways to provide an appropriate mapping.

Each message in the list of messages you pass in should have a

- `role` : This is the role - for now we accept user and assistant
- `content` : content of the message
- `created_at` : This is mostly used for time series analysis

The following code below works and loads the first 2000 entries from the non-toxic wildchat dataset.

```python
from kura.types import Conversation
import os
from datetime import timedelta


def process_messages(row: dict):
    return [
        {
            "role": message["role"],
            "content": message["content"],
            "created_at": row["timestamp"] + timedelta(minutes=5 * i),
        }
        for i, message in enumerate(row["conversation"])
    ]


conversations = Conversation.from_hf_dataset(
    "allenai/WildChat-nontoxic",
    split="train",
    max_conversations=2000,
    chat_id_fn=lambda x: x["conversation_id"],
    created_at_fn=lambda x: x["timestamp"],
    messages_fn=process_messages,
)

kura = Kura()
asyncio.run(kura.cluster_conversations(conversations))

kura.visualise_clusters()
```

## LLM Extractors

> This is currently only supported during the summary step. We'll slowly roll out more support for more flexible LLM Extractors

We also provide support for doing custom analysis and aggregation for metrics using language models or other methods using the `instructor` library. All you need to do is to return an `ExtractedProperty` type

Here's a simple example where we tag the language of the conversation by getting the language model to determine the language code.

```python
import asyncio
import instructor
from pydantic import BaseModel, Field


class Language(BaseModel):
    language_code: str = Field(
        description="The language code of the conversation. (Eg. en, fr, es)",
        pattern=r"^[a-z]{2}$",
    )


async def language_extractor(
    conversation: Conversation,
    sem: asyncio.Semaphore,
    client: instructor.AsyncInstructor,
) -> ExtractedProperty:
    async with sem:
        resp = await client.chat.completions.create(
            model="gemini-2.0-flash",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that extracts the language of the following conversation.",
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

We can then use it in our clustering step with the following code snippets

```python
from kura import Kura
from kura.types import Conversation, ExtractedProperty
from kura.summarisation import SummaryModel

summary_model = SummaryModel(extractors=[language_extractor])
kura = Kura(max_clusters=10, summarisation_model=summary_model)
conversations = Conversation.from_claude_conversation_dump("conversations.json")
asyncio.run(kura.cluster_conversations(conversations))
kura.visualise_clusters()
```

## Technical Walkthrough

I've also recorded a technical deep dive into what Kura is and the ideas behind it if you'd rather watch than read.

<iframe width="560" height="315" src="https://www.youtube.com/embed/TPOP_jDiSVE?si=uvTond4LUwJGOn4F" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## CLI

We provide a simple CLI tool that runs Kura with some default settings and a react frontend with associated visualisation. To boot it up, simply run the following command:

```bash
kura
```

This will in turn start up a local FastAPI server that you can interact with to upload your data and visualise the clusters. It roughly takes ~1 min for ~1000 conversations with a semaphore of around 50 requests at any given time. If you have higher concurrency, you can increase the semaphore to speed up the process.

```bash
> kura
INFO:     Started server process [41539]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**You can combine multiple different conversation files into a single cluster by uploading them all at once.**. We also provide options to modify parameters such as the maximum number of clusters and whether you'd like to rerun the clustering process out of the box.

<!--

- [x] Implement a simple Kura clustering class
- [x] Implement a Kura CLI tool
- [ ] Support hooks that can be ran on individual conversations and clusters to extract metadata
- [ ] Support heatmap visualisation
- [ ] Support ChatGPT conversations
- [ ] Show how we can use Kura with other configurations such as UMAP instead of KMeans earlier on
- [ ] Support more clients/conversation formats
- [ ] Provide support for the specific flag that we can use in the CLi to specify the clustering directory and the port



## Getting Started

!!! note

    Kura ships using the `gemini-1.5-flash` model by default. You must set a `GOOGLE_API_KEY` environment variable in your shell to use the Google Gemini API. If you don't have one, [you can get one here](https://aistudio.google.com/prompts/new_chat).

To get started with Kura, you'll need to install our python package and have a list of conversations to cluster.

=== "pip"

    ```bash
    pip install kura
    ```

=== "uv"

    ```bash
    uv pip install kura
    ```

With your conversations on hand, there are two ways that you can run clustering with Kura.


### Using the Python API

You can also use the Python API to do the same thing.

```python
from kura import Kura
from asyncio import run
from kura.types import Conversation


kura = Kura()
conversations: list[Conversation] = Conversation.from_claude_conversation_dump(
    "conversations.json"
)
run(kura.cluster_conversations(conversations))

```

We assume here that you have a `conversations.json` file in your current working directory which contains data in the format of the Claude Conversation Dump. You can see a guide on how to export your conversation history from the Claude app [here](https://support.anthropic.com/en/articles/9450526-how-can-i-export-my-claude-ai-data).

## Loading Custom Conversations

As mentioned above, if you're using a different formatting for your messages, you can also just manually create a list of `Conversation` objects and pass them into the `cluster_conversations` method. This is useful if you're exporting conversations from a different source.

Let's take the following example of a conversation

```python
conversations = [
    {
        "role": "user",
        "content": "Hello, how are you?"
    },
    {
        "role": "assistant",
        "content": "I'm fine, thank you!"
    }
]
```

We can then manually create a `Conversation` object from this and pass it into the `cluster_conversations` method.

```python
from kura.types import Conversation
from uuid import uuid4

conversation = [
    Conversation(
        messages=[
            Message(
                created_at=str(datetime.now()),
                role=message["role"],
                content=message["content"],
            )
            for message in conversation
        ],
        id=str(uuid4()),
        created_at=datetime.now(),
    )
]

```

Once you've done so, you can then pass this list of conversations into the `cluster_conversations` method.

!!! note

    To run clustering you should have ~100 conversations on hand. If not, the clusters don't really make much sense since the language model will have a hard time generating meaningful clusters of user behaviour

````python
from kura.types import Conversation

conversations: list[Conversation] = Conversation.from_claude_conversation_dump(
    "conversations.json"
)
run(kura.cluster_conversations(conversations))
``` -->
