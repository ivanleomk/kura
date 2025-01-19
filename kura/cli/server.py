from fastapi import FastAPI, staticfiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from kura import Kura
from kura.types import ProjectedCluster, Conversation, Message
from kura.cli.visualisation import (
    generate_cumulative_chart_data,
    generate_messages_per_chat_data,
    generate_messages_per_week_data,
    generate_new_chats_per_week_data,
)
import json
import os

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
    data: list[dict]


@api.post("/api/analyse")
async def analyse_conversations(conversation_data: ConversationData):
    conversations = [
        Conversation(
            chat_id=conversation["uuid"],
            created_at=conversation["created_at"],
            messages=[
                Message(
                    created_at=message["created_at"],
                    role=message["sender"],
                    content="\n".join(
                        [
                            item["text"]
                            for item in message["content"]
                            if item["type"] == "text"
                        ]
                    ),
                )
                for message in conversation["chat_messages"]
            ],
        )
        for conversation in conversation_data.data
    ]

    clusters_file = (
        Path(os.path.abspath(os.environ["KURA_CHECKPOINT_DIR"]))
        / "dimensionality_checkpoints.json"
    )
    clusters = []

    # Load clusters from checkpoint file if it exists

    if not clusters_file.exists():
        kura = Kura(
            checkpoint_dir=str(
                Path(os.path.abspath(os.environ["KURA_CHECKPOINT_DIR"]))
            ),
            conversations=conversations,
        )
        await kura.cluster_conversations()

    with open(clusters_file) as f:
        clusters_data = []
        for line in f:
            clusters_data.append(line)
        clusters = [
            ProjectedCluster(**json.loads(cluster)) for cluster in clusters_data
        ]

    return {
        "cumulative_words": generate_cumulative_chart_data(conversations),
        "messages_per_chat": generate_messages_per_chat_data(conversations),
        "messages_per_week": generate_messages_per_week_data(conversations),
        "new_chats_per_week": generate_new_chats_per_week_data(conversations),
        "clusters": clusters,
    }


# Serve static files from web/dist at the root
web_dir = Path(__file__).parent.parent / "static" / "dist"
if not web_dir.exists():
    raise FileNotFoundError(f"Static files directory not found: {web_dir}")

# Mount static files at root
api.mount("/", staticfiles.StaticFiles(directory=str(web_dir), html=True))
