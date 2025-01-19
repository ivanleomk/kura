from fastapi import FastAPI, staticfiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from kura import Kura
from kura.types import ProjectedCluster, Conversation
from typing import Optional
from kura.cli.visualisation import (
    generate_cumulative_chart_data,
    generate_messages_per_chat_data,
    generate_messages_per_week_data,
    generate_new_chats_per_week_data,
)
import json


api = FastAPI()

# Configure CORS
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Serve static files from web/dist
web_dir = Path(__file__).parent.parent / "static" / "dist"
if not web_dir.exists():
    raise FileNotFoundError(f"Static files directory not found: {web_dir}")


class ConversationData(BaseModel):
    data: list[Conversation]
    max_clusters: Optional[int]
    disable_checkpoints: bool


@api.post("/api/analyse")
async def analyse_conversations(conversation_data: ConversationData):
    print(conversation_data.disable_checkpoints)
    # Load clusters from checkpoint file if it exists
    clusters_file = Path("./checkpoints") / "dimensionality.jsonl"
    if not clusters_file.exists() or conversation_data.disable_checkpoints:
        kura = Kura(
            checkpoint_dir=str(clusters_file.parent),
            max_clusters=conversation_data.max_clusters
            if conversation_data.max_clusters
            else 10,
            disable_checkpoints=conversation_data.disable_checkpoints,
        )
        clusters = await kura.cluster_conversations(conversation_data.data)
    else:
        with open(clusters_file) as f:
            clusters_data = []
            for line in f:
                clusters_data.append(line)
            clusters = [
                ProjectedCluster(**json.loads(cluster)) for cluster in clusters_data
            ]

    return {
        "cumulative_words": generate_cumulative_chart_data(conversation_data.data),
        "messages_per_chat": generate_messages_per_chat_data(conversation_data.data),
        "messages_per_week": generate_messages_per_week_data(conversation_data.data),
        "new_chats_per_week": generate_new_chats_per_week_data(conversation_data.data),
        "clusters": clusters,
    }


# Serve static files from web/dist at the root
web_dir = Path(__file__).parent.parent / "static" / "dist"
if not web_dir.exists():
    raise FileNotFoundError(f"Static files directory not found: {web_dir}")

# Mount static files at root
api.mount("/", staticfiles.StaticFiles(directory=str(web_dir), html=True))
