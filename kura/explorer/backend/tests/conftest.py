"""Test configuration and fixtures."""

import os
import sys
from datetime import datetime
from unittest.mock import Mock
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Set test environment before importing app
os.environ["KURA_CHECKPOINT_DIR"] = "/tmp/test_checkpoints"

# Add the backend directory to Python path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from main import app
    from kura.explorer.api import KuraExplorer
except ImportError as e:
    # Fallback for different import scenarios
    print(f"Import warning: {e}")
    # Create a minimal mock app for testing
    from fastapi import FastAPI

    app = FastAPI()


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
        "max_cluster_level": 3,
    }

    # Mock clusters - create realistic cluster objects
    cluster1 = Mock()
    cluster1.id = "cluster_1"
    cluster1.name = "Python Development"
    cluster1.description = "Questions about Python programming"
    cluster1.level = 0
    cluster1.parent_id = None
    cluster1.x_coord = 0.5
    cluster1.y_coord = 0.3
    cluster1.chat_ids = ["conv1", "conv2", "conv3"]

    cluster2 = Mock()
    cluster2.id = "cluster_2"
    cluster2.name = "Web Development"
    cluster2.description = "Frontend and backend web development"
    cluster2.level = 0
    cluster2.parent_id = None
    cluster2.x_coord = 0.7
    cluster2.y_coord = 0.6
    cluster2.chat_ids = ["conv4", "conv5"]

    cluster3 = Mock()
    cluster3.id = "cluster_3"
    cluster3.name = "Django Framework"
    cluster3.description = "Django-specific questions"
    cluster3.level = 1
    cluster3.parent_id = "cluster_1"
    cluster3.x_coord = 0.4
    cluster3.y_coord = 0.2
    cluster3.chat_ids = ["conv1"]

    sample_clusters = [cluster1, cluster2, cluster3]

    explorer.get_clusters.return_value = sample_clusters

    # Mock detailed cluster
    detailed_cluster = Mock()
    detailed_cluster.id = "cluster_1"
    detailed_cluster.name = "Python Development"
    detailed_cluster.description = "Questions about Python programming"
    detailed_cluster.level = 0
    detailed_cluster.parent_id = None
    detailed_cluster.x_coord = 0.5
    detailed_cluster.y_coord = 0.3
    detailed_cluster.conversation_count = 3
    detailed_cluster.parent = None
    detailed_cluster.children = [cluster3]

    # Mock conversation for cluster
    conv_mock = Mock()
    conv_mock.chat_id = "conv1"
    conv_mock.created_at = datetime(2024, 1, 1)
    conv_mock.metadata_json = {"source": "test"}
    conv_mock.message_count = 10
    detailed_cluster.conversations = [conv_mock]

    explorer.get_cluster.return_value = detailed_cluster
    explorer.get_cluster_hierarchy.return_value = [cluster1]

    # Mock conversations - create realistic conversation objects
    conv1 = Mock()
    conv1.chat_id = "conv1"
    conv1.created_at = datetime(2024, 1, 1)
    conv1.metadata_json = {"source": "web", "user_id": "user123"}
    conv1.message_count = 10

    # Mock cluster objects for conversations
    cluster_mock = Mock()
    cluster_mock.name = "Python Development"
    conv1.clusters = [cluster_mock]

    conv2 = Mock()
    conv2.chat_id = "conv2"
    conv2.created_at = datetime(2024, 1, 2)
    conv2.metadata_json = {"source": "api", "user_id": "user456"}
    conv2.message_count = 15

    cluster_mock2 = Mock()
    cluster_mock2.name = "Web Development"
    conv2.clusters = [cluster_mock2]

    sample_conversations = [conv1, conv2]

    explorer.get_conversations.return_value = sample_conversations

    # Mock detailed conversation
    detailed_conv = Mock()
    detailed_conv.id = "conv1"
    detailed_conv.created_at = datetime(2024, 1, 1)
    detailed_conv.metadata = {"source": "web", "user_id": "user123"}

    # Mock messages
    msg1 = Mock()
    msg1.id = 1
    msg1.conversation_id = "conv1"
    msg1.created_at = datetime(2024, 1, 1)
    msg1.role = "user"
    msg1.content = "How do I use pandas?"

    msg2 = Mock()
    msg2.id = 2
    msg2.conversation_id = "conv1"
    msg2.created_at = datetime(2024, 1, 1)
    msg2.role = "assistant"
    msg2.content = "Pandas is a data manipulation library..."

    detailed_conv.messages = [msg1, msg2]

    # Mock summary
    summary_mock = Mock()
    summary_mock.chat_id = "conv1"
    summary_mock.summary = "User asked about pandas usage"
    summary_mock.languages = ["python"]
    summary_mock.task = "data_analysis"
    summary_mock.user_frustration = 2
    summary_mock.concerning_score = 1
    summary_mock.assistant_errors = []
    detailed_conv.summary = summary_mock

    detailed_conv.clusters = [cluster_mock]

    explorer.get_conversation.return_value = detailed_conv

    # Mock summary retrieval
    explorer.get_summary.return_value = summary_mock

    # Mock search results
    explorer.search_conversations.return_value = [conv1]

    # Add engine attribute for database session mocking
    explorer.engine = Mock()

    return explorer


@pytest.fixture
def client(mock_explorer):
    """Create FastAPI test client with mocked explorer."""
    # Patch the global explorer
    try:
        import main

        original_explorer = getattr(main, "explorer", None)
        main.explorer = mock_explorer

        client = TestClient(app)
        yield client

        # Restore original explorer
        main.explorer = original_explorer
    except ImportError:
        # Fallback if main module isn't available
        with pytest.MonkeyPatch().context() as m:
            m.setattr("main.explorer", mock_explorer)
            client = TestClient(app)
            yield client


@pytest.fixture
async def async_client(mock_explorer):
    """Create async test client with mocked explorer."""
    try:
        import main

        original_explorer = getattr(main, "explorer", None)
        main.explorer = mock_explorer

        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

        main.explorer = original_explorer
    except ImportError:
        # Fallback if main module isn't available
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac


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
        "languages": ["python"],
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
            "user_frustration": 2,
        },
        "cluster_names": ["Python Development"],
    }
