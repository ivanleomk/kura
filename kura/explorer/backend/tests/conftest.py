"""Test configuration and fixtures."""

import os
from typing import Generator, Dict, Any
from datetime import datetime
from unittest.mock import Mock, MagicMock

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Set test environment before importing app
os.environ["KURA_CHECKPOINT_DIR"] = "/tmp/test_checkpoints"

from main import app
from kura.explorer.api import KuraExplorer


@pytest.fixture
def mock_explorer():
    """Create a mock KuraExplorer instance with sample data."""
    explorer = Mock(spec=KuraExplorer)
    
    # Mock stats
    explorer.get_stats.return_value = {
        "total_conversations": 100,
        "total_messages": 500,
        "total_summaries": 95,
        "total_clusters": 25,
        "root_clusters": 5,
        "max_cluster_level": 3
    }
    
    # Mock clusters
    sample_clusters = [
        Mock(
            id="cluster_1",
            name="Python Development",
            description="Questions about Python programming",
            level=0,
            parent_id=None,
            x_coord=0.5,
            y_coord=0.3,
            chat_ids=["conv1", "conv2", "conv3"]
        ),
        Mock(
            id="cluster_2", 
            name="Web Development",
            description="Frontend and backend web development",
            level=0,
            parent_id=None,
            x_coord=0.7,
            y_coord=0.6,
            chat_ids=["conv4", "conv5"]
        ),
        Mock(
            id="cluster_3",
            name="Django Framework",
            description="Django-specific questions",
            level=1,
            parent_id="cluster_1",
            x_coord=0.4,
            y_coord=0.2,
            chat_ids=["conv1"]
        )
    ]
    
    explorer.get_clusters.return_value = sample_clusters
    explorer.get_cluster.return_value = Mock(
        id="cluster_1",
        name="Python Development", 
        description="Questions about Python programming",
        level=0,
        parent_id=None,
        x_coord=0.5,
        y_coord=0.3,
        conversation_count=3,
        parent=None,
        children=[sample_clusters[2]],
        conversations=[
            Mock(
                chat_id="conv1",
                created_at=datetime(2024, 1, 1),
                metadata_json={"source": "test"},
                message_count=10
            )
        ]
    )
    
    explorer.get_cluster_hierarchy.return_value = [sample_clusters[0]]
    
    # Mock conversations
    sample_conversations = [
        Mock(
            chat_id="conv1",
            created_at=datetime(2024, 1, 1),
            metadata_json={"source": "web", "user_id": "user123"},
            message_count=10,
            clusters=[sample_clusters[0]]
        ),
        Mock(
            chat_id="conv2", 
            created_at=datetime(2024, 1, 2),
            metadata_json={"source": "api", "user_id": "user456"},
            message_count=15,
            clusters=[sample_clusters[1]]
        )
    ]
    
    explorer.get_conversations.return_value = sample_conversations
    explorer.get_conversation.return_value = Mock(
        id="conv1",
        created_at=datetime(2024, 1, 1),
        metadata={"source": "web", "user_id": "user123"},
        messages=[
            Mock(
                id=1,
                conversation_id="conv1",
                created_at=datetime(2024, 1, 1),
                role="user",
                content="How do I use pandas?"
            ),
            Mock(
                id=2,
                conversation_id="conv1", 
                created_at=datetime(2024, 1, 1),
                role="assistant",
                content="Pandas is a data manipulation library..."
            )
        ],
        summary=Mock(
            chat_id="conv1",
            summary="User asked about pandas usage",
            languages=["python"],
            task="data_analysis",
            user_frustration=2,
            concerning_score=1,
            assistant_errors=[]
        ),
        clusters=[sample_clusters[0]]
    )
    
    # Mock summaries
    explorer.get_summary.return_value = Mock(
        chat_id="conv1",
        summary="User asked about pandas usage",
        request="How to use pandas",
        languages=["python"],
        task="data_analysis", 
        user_frustration=2,
        concerning_score=1,
        assistant_errors=[],
        metadata={}
    )
    
    # Mock search
    explorer.search_conversations.return_value = {
        "conversations": sample_conversations[:1],
        "total_count": 1
    }
    
    return explorer


@pytest.fixture
def client(mock_explorer):
    """Create FastAPI test client with mocked explorer."""
    # Patch the global explorer
    import main
    original_explorer = main.explorer
    main.explorer = mock_explorer
    
    client = TestClient(app)
    yield client
    
    # Restore original explorer
    main.explorer = original_explorer


@pytest.fixture
async def async_client(mock_explorer):
    """Create async test client with mocked explorer."""
    import main
    original_explorer = main.explorer
    main.explorer = mock_explorer
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    main.explorer = original_explorer


@pytest.fixture
def sample_cluster_data():
    """Sample cluster data for testing."""
    return {
        "id": "cluster_1",
        "name": "Python Development",
        "description": "Questions about Python programming",
        "level": 0,
        "parent_id": None,
        "conversation_count": 3,
        "child_count": 1,
        "avg_frustration": 2.5,
        "languages": ["python"]
    }


@pytest.fixture
def sample_conversation_data():
    """Sample conversation data for testing."""
    return {
        "id": "conv1",
        "created_at": "2024-01-01T00:00:00",
        "metadata": {"source": "web", "user_id": "user123"},
        "message_count": 10,
        "summary": {
            "chat_id": "conv1",
            "summary": "User asked about pandas usage",
            "languages": ["python"],
            "task": "data_analysis",
            "user_frustration": 2
        },
        "cluster_names": ["Python Development"]
    } 