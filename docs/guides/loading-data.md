# Loading Data

Kura supports multiple data sources and formats for loading conversational data. This guide explains the different methods available.

## Supported Data Sources

Kura provides built-in support for:

1. Claude conversation exports
2. Hugging Face datasets
3. Custom conversation objects

## From Claude Conversation Exports

If you're using Claude, you can export your conversation history and load it directly into Kura:

```python
from kura import Kura
from kura.types import Conversation
import asyncio

# Load conversations from Claude export
conversations = Conversation.from_claude_conversation_dump("conversations.json")

# Initialize Kura and process conversations
kura = Kura()
asyncio.run(kura.cluster_conversations(conversations))
```

To export your Claude conversations:
1. Visit [Claude](https://claude.ai)
2. Click on your profile/settings
3. Navigate to "Export Data"
4. Download your conversation history
5. Save the file as "conversations.json"

## From Hugging Face Datasets

Kura can load data from any Hugging Face dataset containing conversational data:

```python
from kura import Kura
from kura.types import Conversation
import asyncio

# Load conversations from Hugging Face
conversations = Conversation.from_hf_dataset(
    "ivanleomk/synthetic-gemini-conversations",
    split="train",
    max_conversations=2000  # Optional: limit the number of conversations
)

# Initialize Kura and process conversations
kura = Kura()
asyncio.run(kura.cluster_conversations(conversations))
```

#### Example Dataset: ivanleomk/synthetic-gemini-conversations

This example dataset is used throughout Kura's documentation and contains:

- **Size**: Approximately 190 conversations
- **Content**: Synthetic technical support and programming discussions
- **Topics**: Web development (Django, React, Spring), software engineering, database design
- **Structure**: Pre-formatted with conversation IDs, timestamps, and message roles compatible with Kura
- **Purpose**: Demonstrates clustering patterns across related programming topics

This dataset is ideal for learning how to use Kura because it:
1. Contains enough conversations to form meaningful clusters
2. Has distinct but related topics for hierarchical clustering 
3. Matches Kura's expected data schema
4. Is small enough to process quickly

### Custom Mapping Functions

If your dataset doesn't match Kura's expected format, you can provide mapping functions:

```python
from kura.types import Conversation
from datetime import timedelta

# Load with custom mapping
conversations = Conversation.from_hf_dataset(
    "allenai/WildChat-nontoxic",
    split="train",
    # Custom mapping functions
    chat_id_fn=lambda x: x["conversation_id"],
    created_at_fn=lambda x: x["timestamp"],
    messages_fn=lambda row: [
        {
            "role": msg["role"],
            "content": msg["content"],
            "created_at": row["timestamp"] + timedelta(minutes=5 * i),
        }
        for i, msg in enumerate(row["conversation"])
    ],
    metadata_fn=lambda x: {"model": x["model"], "toxic": x["toxic"]},
)
```

### Expected Format

By default, Kura expects the following columns in Hugging Face datasets:

| Column | Description |
|--------|-------------|
| `chat_id` | Unique identifier for each conversation |
| `created_at` | Timestamp for when the conversation was created |
| `content` | Messages in the conversation |

## From Custom Data Sources

For other data sources, you can create `Conversation` objects directly:

```python
from kura.types import Conversation, Message
from datetime import datetime
from uuid import uuid4

# Create conversation objects manually
conversations = [
    Conversation(
        messages=[
            Message(
                created_at=str(datetime.now()),
                role="user",
                content="Hello, can you help me with a programming question?"
            ),
            Message(
                created_at=str(datetime.now()),
                role="assistant",
                content="Of course! What programming question do you have?"
            ),
            # ... more messages
        ],
        id=str(uuid4()),
        created_at=datetime.now(),
        metadata={"source": "custom", "category": "programming"}
    )
]

# Initialize Kura and process conversations
kura = Kura()
asyncio.run(kura.cluster_conversations(conversations))
```

### Required Fields

When creating conversations manually, each conversation requires:

- `id`: A unique identifier (string)
- `created_at`: Timestamp for the conversation
- `messages`: List of Message objects, each with:
  - `role`: Either "user" or "assistant"
  - `content`: The text content of the message
  - `created_at`: Timestamp for the message

## Filtering and Preprocessing

You can filter or preprocess conversations before clustering:

```python
# Filter conversations by date
from datetime import datetime, timedelta
one_month_ago = datetime.now() - timedelta(days=30)

recent_conversations = [
    conv for conv in conversations 
    if conv.created_at > one_month_ago
]

# Filter by minimum number of messages
substantive_conversations = [
    conv for conv in conversations 
    if len(conv.messages) >= 3
]

# Filter by content
programming_conversations = [
    conv for conv in conversations 
    if any("python" in msg.content.lower() for msg in conv.messages)
]
```

## Loading Large Datasets

For large datasets, consider:

1. **Processing in batches**: Split your dataset into smaller chunks
2. **Using checkpoints**: Enable checkpointing to resume processing
3. **Sampling**: Start with a representative sample to tune parameters

```python
# Process in batches of 1000 conversations
batch_size = 1000
for i in range(0, len(all_conversations), batch_size):
    kura = Kura(checkpoint_dir=f"./checkpoints_batch_{i//batch_size}")
    asyncio.run(kura.cluster_conversations(all_conversations[i:i+batch_size]))
```

## Next Steps

Now that you know how to load data into Kura, you might want to:

- [Work with metadata](metadata.md) to enrich your analysis
- [Customize models](custom-models.md) for your specific use case
- [Visualize your results](visualization.md) to gain insights