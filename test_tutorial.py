from kura import Kura
from kura.types import Conversation
from kura.embedding import OpenAIEmbeddingModel
from kura.summarisation import SummaryModel
import asyncio
import os
import subprocess
from openai import AsyncOpenAI
import instructor

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

# Create and configure Kura instance with OpenAI models
openai_client = instructor.from_openai(AsyncOpenAI(), use_async=True)
kura = Kura(
    embedding_model=OpenAIEmbeddingModel(),
    summarisation_model=SummaryModel(
        model="openai/gpt-4-turbo-preview",  # Use GPT-4 for summarization
        concurrent_requests=50,  # Configure concurrent requests
        client=openai_client
    ),
    max_clusters=10,
    checkpoint_dir="./tutorial_checkpoints",
    override_checkpoint_dir=True
)

subprocess.run(["kura"]) 