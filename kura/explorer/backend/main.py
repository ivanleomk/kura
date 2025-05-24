"""FastAPI backend for Kura Explorer."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel

from routers import clusters, conversations, search
from kura.explorer.api import KuraExplorer


# Global explorer instance
explorer: Optional[KuraExplorer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize explorer on startup."""
    global explorer
    checkpoint_dir = os.environ.get("KURA_CHECKPOINT_DIR", "./checkpoints")
    print(f"Loading checkpoint data from {checkpoint_dir}...")
    explorer = KuraExplorer(checkpoint_dir)
    yield
    # Cleanup
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Kura Explorer API",
    description="API for exploring Kura checkpoint data",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(clusters.router, prefix="/api/clusters", tags=["clusters"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
app.include_router(search.router, prefix="/api/search", tags=["search"])


from kura.explorer.backend.models import StatsResponse


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    explorer_initialized: bool
    checkpoint_dir: str


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Check API health status.
    
    Returns the current health status of the API and whether the explorer
    has been properly initialized with checkpoint data.
    """
    return HealthResponse(
        status="healthy",
        explorer_initialized=explorer is not None,
        checkpoint_dir=os.environ.get("KURA_CHECKPOINT_DIR", "./checkpoints")
    )


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get overall statistics about the checkpoint data.
    
    Returns counts of conversations, messages, summaries, clusters,
    and other aggregate metrics.
    """
    if not explorer:
        raise HTTPException(status_code=503, detail="Explorer not initialized")
    
    stats = explorer.get_stats()
    return StatsResponse(**stats)