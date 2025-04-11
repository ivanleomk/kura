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
import os

from kura.types.summarisation import ConversationSummary


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


# Serve static files from web/dist at the root
web_dir = Path(__file__).parent.parent / "static" / "dist"
if not web_dir.exists():
    raise FileNotFoundError(f"Static files directory not found: {web_dir}")

# Mount static files at root
api.mount("/", staticfiles.StaticFiles(directory=str(web_dir), html=True))
