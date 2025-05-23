import time
import asyncio
import os
import subprocess
from contextlib import contextmanager
from typing import Dict, List

import rich

@contextmanager
def timer(description: str):
    """Context manager that times an operation."""
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    print(f"[COMPLETED] {description}: {elapsed:.2f}s")

def show_welcome():
    """Display a welcome message."""
    print("\n=== Welcome to Kura Tutorial ===\n")

def show_section_header(title: str, emoji: str = ""):
    """Display a section header."""
    print(f"\n{title}")
    print("─" * len(title))

# Display welcome message
show_welcome()

# Import modules
show_section_header("Module Imports")

with timer("Importing kura modules"):
    from kura import Kura
    from kura.cluster import ClusterModel
    from kura.meta_cluster import MetaClusterModel
    from kura.summarisation import SummaryModel
    from kura.types import Conversation

print("All kura modules imported successfully!\n")

# Configuration section
show_section_header("Configuration")

print("Configuring Kura instance...")

from rich.console import Console

kura = Kura(
    max_clusters=10,
    checkpoint_dir="./tutorial_checkpoints",
    override_checkpoint_dir=True,
    model="openai/gpt-4.1",
    max_concurrent_requests=50,
    console=Console(),
)

print("Kura instance configured successfully!\n")

# Data loading section
show_section_header("Data Loading")

with timer("Loading sample conversations"):
    conversations = Conversation.from_hf_dataset(
        "ivanleomk/synthetic-gemini-conversations",
        split="train"
    )

print(f"Loaded {len(conversations)} conversations successfully!\n")

# Sample conversation examination
show_section_header("Sample Data Examination")

sample_conversation = conversations[0]

# Print conversation details
print("Sample Conversation Details:")
print(f"Chat ID: {sample_conversation.chat_id}")
print(f"Created At: {sample_conversation.created_at}")
print(f"Number of Messages: {len(sample_conversation.messages)}")
print()

# Sample messages
print("Sample Messages:")
for i, msg in enumerate(sample_conversation.messages[:3]):
    content_preview = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
    print(f"  {msg.role}: {content_preview}")

print()

# Processing section
show_section_header("Conversation Processing")

print("Starting conversation clustering...")

async def process_with_progress():
    """Process conversations with a progress indicator."""
    print("Processing conversations with AI models...")
    clustered_data = await kura.cluster_conversations(conversations)
    return clustered_data

clustered_data = asyncio.run(process_with_progress())

print(f"Generated {len(clustered_data)} projected clusters!\n")

# Visualization section
show_section_header("Results Visualization")

print("Generating cluster visualization...")
kura.visualise_clusters_rich()
print("Cluster visualization complete!\n")

# Server startup section
show_section_header("Web Server")
