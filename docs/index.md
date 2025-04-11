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
from kura import Kura
import asyncio
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

## Metadata

> Metadata is only extracted for now during the summarisation step. If there's demand, we can roll out support for this in subsequent steps.

When analysing topic clusters, it's important to look at specific metadata filters within the clusters themselves. We support filtering by these specific metadata filters on the frontend UI that `kura` ships with.

Metadata filters helps us identify specific trends and areas to hone in on. We currently support two main ways of providing metadata

1. `LLM Extractors` : These are functions that run on the raw conversations using `instructor` and return a `ExtractedProperty` type object. Note that you can run any arbitrary code here, it does not have to be a LLM call!
2. `Conversation Metadata` : This is metadata that comes with your own conversations, (Eg. the model used, toxic filters etc) which you can populate when creating the `Conversation` object.

### LLM Extractors

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
    sems: dict[str, asyncio.Semaphore],
    clients: dict[str, instructor.AsyncInstructor],
) -> ExtractedProperty:
    # Get the default semaphore and client limits
    sem = sems.get("default")
    client = clients.get("default")

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

=== "Using Our Extractor"

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

=== "Full Code"

    ```python
    import asyncio
    import instructor
    from pydantic import BaseModel, Field
    from kura import Kura
    from kura.types import Conversation, ExtractedProperty
    from kura.summarisation import SummaryModel


    class Language(BaseModel):
        language_code: str = Field(
            description="The language code of the conversation. (Eg. en, fr, es)",
            pattern=r"^[a-z]{2}$",
        )


    async def language_extractor(
        conversation: Conversation,
        sems: dict[str, asyncio.Semaphore],
        clients: dict[str, instructor.AsyncInstructor],
    ) -> ExtractedProperty:
        # Get the default semaphore and client limits
        sem = sems.get("default")
        client = clients.get("default")

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


    summary_model = SummaryModel(extractors=[language_extractor])
    kura = Kura(
        max_clusters=10, summarisation_model=summary_model, override_checkpoint_dir=True
    )
    conversations = Conversation.from_claude_conversation_dump("conversations.json")[:100]
    asyncio.run(kura.cluster_conversations(conversations))
    kura.visualise_clusters()
    ```

Note that you can also run any arbitrary code within these extractors themselves, we just supply a Semaphore, a Client and the raw `Conversation` object for you to use.

???+ tip

    Make sure to use separate Semaphores for each provider/service you're using and an async compatible client. This will allow you to process your data quickly and effeciently

Here's an example where we provide a new OpenAI Async Client to our Summary model with separate rate limits with a rate limit of 100 concurrent requests for the moderations endpoint

```python
import asyncio
import instructor
from pydantic import BaseModel, Field
from kura import Kura
from kura.types import Conversation, ExtractedProperty
from kura.summarisation import SummaryModel
from openai import AsyncOpenAI
from google.genai import Client


async def moderation_hook(
    conversation: Conversation,
    sems: dict[str, asyncio.Semaphore],
    clients: dict[str, instructor.AsyncInstructor],
) -> ExtractedProperty:
    # Get the default semaphore and client limits
    sem = sems.get("openai")
    client = clients.get("openai")

    async with sem:
        assert isinstance(client, AsyncOpenAI)
        resp = await client.moderations.create(
            model="omni-moderation-latest",
            input="\n".join([message.content for message in conversation.messages]),
        )
        return [
            ExtractedProperty(
                name="moderation_hate",
                value=resp.results[0].categories.hate,
            ),
            ExtractedProperty(
                name="moderation_hate_score",
                value=resp.results[0].category_scores.hate,
            ),
        ] # You can return a list or just a normal ExtractedProperty object here
```

You can then use the extractor as seen below inside the summary model. This gives you the flexibility to define different rate limits and use clients (Eg. Amazon Bedrock, Claude, OpenAI ) depending on your current usage patterns.

=== "Using Our Extractor"

    ```python
    summary_model = SummaryModel(
        extractors=[moderation_hook],
        clients={
            "default": instructor.from_genai(Client(), use_async=True),
            "openai": AsyncOpenAI(),
        },
        concurrent_requests={
            "openai": 100,
            "default": 50,
        },
    )
    kura = Kura(
        max_clusters=10, summarisation_model=summary_model, override_checkpoint_dir=True
    )
    conversations = Conversation.from_claude_conversation_dump("conversations.json")
    asyncio.run(kura.cluster_conversations(conversations))
    kura.visualise_clusters()
    ```

=== "Full Code"

    ```python
    import asyncio
    import instructor
    from pydantic import BaseModel, Field
    from kura import Kura
    from kura.types import Conversation, ExtractedProperty
    from kura.summarisation import SummaryModel
    from openai import AsyncOpenAI
    from google.genai import Client


    async def moderation_hook(
        conversation: Conversation,
        sems: dict[str, asyncio.Semaphore],
        clients: dict[str, instructor.AsyncInstructor],
    ) -> ExtractedProperty:
        # Get the default semaphore and client limits
        sem = sems.get("openai")
        client = clients.get("openai")

        async with sem:
            assert isinstance(client, AsyncOpenAI)
            resp = await client.moderations.create(
                model="omni-moderation-latest",
                input="\n".join([message.content for message in conversation.messages]),
            )
            return [
                ExtractedProperty(
                    name="moderation_hate",
                    value=resp.results[0].categories.hate,
                ),
                ExtractedProperty(
                    name="moderation_hate_score",
                    value=resp.results[0].category_scores.hate,
                ),
            ]


    summary_model = SummaryModel(
        extractors=[moderation_hook],
        clients={
            "default": instructor.from_genai(Client(), use_async=True),
            "openai": AsyncOpenAI(),
        },
        concurrent_requests={
            "openai": 100,
            "default": 50,
        },
    )
    kura = Kura(
        max_clusters=10, summarisation_model=summary_model, override_checkpoint_dir=True
    )
    conversations = Conversation.from_claude_conversation_dump("conversations.json")[:2]
    asyncio.run(kura.cluster_conversations(conversations))
    kura.visualise_clusters()
    ```

### Conversation Metadata

Sometimes you might have metadata that you'll like to preserve which is specific to the conversation object (Eg. model used, user account details, org Id). In this case, you can just do so with the metadata field on the `Conversation` object.

Here's a quick example using the `allenai/WildChat-nontoxic` dataset where we store the model used and the classification of the chat's toxicity and harmfulness.

```python
from kura.types import Conversation
from kura import Kura
import asyncio
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
    max_conversations=10,
    chat_id_fn=lambda x: x["conversation_id"],
    created_at_fn=lambda x: x["timestamp"],
    messages_fn=process_messages,
    metadata_fn=lambda x: {
        "model": x["model"],
        "toxic": x["toxic"],
        "redacted": x["redacted"], # Using the metadata fn here
    },
)

kura = Kura(override_checkpoint_dir=True)
asyncio.run(kura.cluster_conversations(conversations))

kura.visualise_clusters()
```

You can also just set it on the `Conversation` object's `metadata` field.

## Technical Walkthrough

I've also recorded a technical deep dive into what Kura is and the ideas behind it if you'd rather watch than read.

<iframe width="560" height="315" src="https://www.youtube.com/embed/TPOP_jDiSVE?si=uvTond4LUwJGOn4F" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## Visualisations

We provide some simple visualisation tools that you can use to view the results of your Kura clustering.

### React Application

!!! note

    Make sure to run Kura on your dataset of choice prior to this. The frontend application simply loads and visualises the clusters for you that we've saved in your desired checkpoint directory

Simply run the command below and you'll be able to visualise the clusters that we've generated

```bash
kura

Access website at (http://localhost:8000)

INFO:     Started server process [30548]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:49496 - "GET / HTTP/1.1" 200 OK
```

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
