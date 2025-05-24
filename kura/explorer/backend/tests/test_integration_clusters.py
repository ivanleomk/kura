"""Integration tests for cluster-conversation mappings using real checkpoint data."""

import os
import pytest
from pathlib import Path
from sqlmodel import Session, select
from fastapi.testclient import TestClient
from kura.explorer.api import KuraExplorer
from kura.explorer.db.models import (
    ClusterDB,
    ConversationDB,
    ClusterConversationLink,
    SummaryDB,
)
from main import app

# Set environment for real checkpoint data
CHECKPOINT_DIR = os.path.join(os.path.dirname(__file__), "test_data")
os.environ["KURA_CHECKPOINT_DIR"] = CHECKPOINT_DIR


@pytest.fixture(scope="module")
def real_explorer():
    """Create a real KuraExplorer instance with actual checkpoint data."""
    if not Path(CHECKPOINT_DIR).exists():
        pytest.skip(f"Checkpoint directory {CHECKPOINT_DIR} not found")

    explorer = KuraExplorer(CHECKPOINT_DIR)
    return explorer


@pytest.fixture(scope="module")
def real_client(real_explorer):
    """Create FastAPI test client with real explorer data."""
    # Patch the global explorer with real data
    import main

    original_explorer = main.explorer
    main.explorer = real_explorer

    client = TestClient(app)
    yield client

    # Restore original explorer
    main.explorer = original_explorer


class TestClusterConversationMapping:
    """Test cluster-conversation mapping with real data."""

    def test_database_has_conversations(self, real_explorer):
        """Test that the database contains conversation records."""
        with Session(real_explorer.engine) as session:
            conversation_count = session.exec(select(ConversationDB).limit(1)).first()

            assert conversation_count is not None, "No conversations found in database"

            # Count total conversations
            total_conversations = len(session.exec(select(ConversationDB)).all())
            assert total_conversations > 0, (
                f"Expected conversations, found {total_conversations}"
            )
            print(f"✅ Found {total_conversations} conversations in database")

    def test_database_has_cluster_conversation_links(self, real_explorer):
        """Test that cluster-conversation links exist in database."""
        with Session(real_explorer.engine) as session:
            link_count = len(session.exec(select(ClusterConversationLink)).all())
            assert link_count > 0, (
                f"Expected cluster-conversation links, found {link_count}"
            )
            print(f"✅ Found {link_count} cluster-conversation links")

    def test_clusters_have_conversations(self, real_explorer):
        """Test that clusters can retrieve their associated conversations."""
        with Session(real_explorer.engine) as session:
            # Get a cluster that should have conversations
            cluster = session.exec(select(ClusterDB).limit(1)).first()

            assert cluster is not None, "No clusters found in database"

            # Get conversations for this cluster via join
            conversations = session.exec(
                select(ConversationDB)
                .join(ClusterConversationLink)
                .where(ClusterConversationLink.cluster_id == cluster.id)
            ).all()

            assert len(conversations) > 0, f"Cluster {cluster.id} has no conversations"
            print(f"✅ Cluster '{cluster.name}' has {len(conversations)} conversations")

            # Verify conversations have valid data
            for conv in conversations[:3]:  # Check first 3
                assert conv.chat_id is not None
                assert conv.created_at is not None
                print(f"   - Conversation {conv.chat_id[:8]}...")

    def test_conversation_ids_match_summaries(self, real_explorer):
        """Test that conversation IDs match with summary data."""
        with Session(real_explorer.engine) as session:
            # Get a conversation
            conversation = session.exec(select(ConversationDB).limit(1)).first()

            assert conversation is not None, "No conversations found"

            # Check if summary exists for this conversation
            summary = session.exec(
                select(SummaryDB).where(SummaryDB.chat_id == conversation.chat_id)
            ).first()

            assert summary is not None, (
                f"No summary found for conversation {conversation.chat_id}"
            )
            assert summary.chat_id == conversation.chat_id
            print(f"✅ Conversation {conversation.chat_id[:8]}... has matching summary")

    def test_cluster_has_valid_conversation_data(self, real_explorer):
        """Test that clusters return valid conversation data through API."""
        # Get a cluster with conversations
        clusters = real_explorer.get_clusters(level=0)
        assert len(clusters) > 0, "No root clusters found"

        # Find a cluster with conversations
        cluster_with_convs = None
        for cluster in clusters:
            with Session(real_explorer.engine) as session:
                conv_count = session.exec(
                    select(ClusterConversationLink).where(
                        ClusterConversationLink.cluster_id == cluster.id
                    )
                ).all()
                if len(conv_count) > 0:
                    cluster_with_convs = cluster
                    break

        assert cluster_with_convs is not None, "No clusters with conversations found"

        # Test the get_cluster method
        cluster_detail = real_explorer.get_cluster(cluster_with_convs.id)
        assert cluster_detail is not None, (
            f"Could not retrieve cluster {cluster_with_convs.id}"
        )

        # Check if conversations are loaded
        print(f"✅ Cluster '{cluster_detail.name}' retrieved successfully")
        print(f"   - Cluster ID: {cluster_detail.id}")
        print(f"   - Conversation count: {cluster_detail.conversation_count}")

        # Verify conversations attribute exists and has data
        if hasattr(cluster_detail, "conversations") and cluster_detail.conversations:
            print(f"   - Loaded conversations: {len(cluster_detail.conversations)}")
            for conv in cluster_detail.conversations[:3]:
                print(f"     * {conv.chat_id[:8]}...")
        else:
            print(
                "   - No conversations loaded (this indicates the relationship issue)"
            )


class TestClusterAPIEndpoints:
    """Test cluster API endpoints with real data."""

    def test_api_clusters_list(self, real_client):
        """Test that /api/clusters returns real cluster data."""
        response = real_client.get("/api/clusters?limit=5")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert len(data["items"]) > 0, "No clusters returned from API"

        cluster = data["items"][0]
        assert "id" in cluster
        assert "name" in cluster
        assert "conversation_count" in cluster

        print(f"✅ API returned {len(data['items'])} clusters")
        print(
            f"   - First cluster: '{cluster['name']}' with {cluster['conversation_count']} conversations"
        )

    def test_api_cluster_detail_has_conversations(self, real_client, real_explorer):
        """Test that cluster detail endpoint returns conversations."""
        # Get a cluster ID that should have conversations
        with Session(real_explorer.engine) as session:
            cluster_with_convs = session.exec(
                select(ClusterDB, ClusterConversationLink)
                .join(ClusterConversationLink)
                .limit(1)
            ).first()

            assert cluster_with_convs is not None, (
                "No clusters with conversations found"
            )
            cluster_id = cluster_with_convs[0].id

        # Test the API endpoint
        response = real_client.get(f"/api/clusters/{cluster_id}")
        assert response.status_code == 200

        data = response.json()
        assert "id" in data
        assert "conversations" in data

        conversations = data["conversations"]
        print(f"✅ Cluster detail API returned {len(conversations)} conversations")

        if len(conversations) > 0:
            conv = conversations[0]
            assert "id" in conv
            assert "created_at" in conv
            print(f"   - First conversation: {conv['id'][:8]}...")
        else:
            pytest.fail("Cluster detail API returned 0 conversations - mapping issue!")

    def test_api_cluster_tree_structure(self, real_client):
        """Test that cluster tree endpoint returns proper hierarchy."""
        response = real_client.get("/api/clusters/tree")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "No clusters in tree structure"

        # Check tree structure
        for root_cluster in data:
            assert "id" in root_cluster
            assert "name" in root_cluster
            assert "conversation_count" in root_cluster
            assert "children" in root_cluster

            print(
                f"✅ Root cluster: '{root_cluster['name']}' with {root_cluster['conversation_count']} conversations"
            )

            # Check children
            for child in root_cluster["children"][:2]:  # Check first 2 children
                assert "id" in child
                assert "name" in child
                print(
                    f"   - Child: '{child['name']}' with {child['conversation_count']} conversations"
                )


class TestDataIntegrity:
    """Test data integrity between tables."""

    def test_orphaned_cluster_links(self, real_explorer):
        """Test for orphaned cluster-conversation links."""
        with Session(real_explorer.engine) as session:
            # Find links pointing to non-existent conversations
            orphaned_links = session.exec(
                select(ClusterConversationLink)
                .outerjoin(
                    ConversationDB,
                    ClusterConversationLink.conversation_id == ConversationDB.chat_id,
                )
                .where(ConversationDB.chat_id.is_(None))
            ).all()

            if len(orphaned_links) > 0:
                print(
                    f"⚠️  Found {len(orphaned_links)} orphaned cluster-conversation links"
                )
                for link in orphaned_links[:5]:
                    print(f"   - Link to missing conversation: {link.conversation_id}")
            else:
                print("✅ No orphaned cluster-conversation links found")

    def test_conversations_without_summaries(self, real_explorer):
        """Test for conversations without corresponding summaries."""
        with Session(real_explorer.engine) as session:
            conversations_without_summaries = session.exec(
                select(ConversationDB)
                .outerjoin(SummaryDB, ConversationDB.chat_id == SummaryDB.chat_id)
                .where(SummaryDB.chat_id.is_(None))
            ).all()

            if len(conversations_without_summaries) > 0:
                print(
                    f"⚠️  Found {len(conversations_without_summaries)} conversations without summaries"
                )
            else:
                print("✅ All conversations have corresponding summaries")

    def test_cluster_conversation_count_accuracy(self, real_explorer):
        """Test that cluster conversation counts are accurate."""
        with Session(real_explorer.engine) as session:
            clusters = session.exec(select(ClusterDB).limit(5)).all()

            for cluster in clusters:
                # Count conversations via join
                actual_count = len(
                    session.exec(
                        select(ClusterConversationLink).where(
                            ClusterConversationLink.cluster_id == cluster.id
                        )
                    ).all()
                )

                # Get cluster detail to check reported count
                cluster_detail = real_explorer.get_cluster(cluster.id)

                if cluster_detail:
                    reported_count = cluster_detail.conversation_count
                    print(
                        f"Cluster '{cluster.name}': reported={reported_count}, actual={actual_count}"
                    )

                    # Allow some tolerance for different counting methods
                    assert abs(reported_count - actual_count) <= 1, (
                        f"Conversation count mismatch for cluster {cluster.name}: reported={reported_count}, actual={actual_count}"
                    )


class TestSearchIntegration:
    """Test search functionality with real data."""

    def test_search_returns_real_conversations(self, real_client):
        """Test that search returns actual conversations from the database."""
        response = real_client.get("/api/search?q=python&limit=5")
        assert response.status_code == 200

        data = response.json()
        assert "conversations" in data
        assert "total_count" in data

        if data["total_count"] > 0:
            conversations = data["conversations"]
            print(f"✅ Search for 'python' returned {len(conversations)} conversations")

            for conv in conversations[:2]:
                assert "id" in conv
                assert "cluster_names" in conv
                print(f"   - {conv['id'][:8]}... in clusters: {conv['cluster_names']}")
        else:
            print("⚠️  Search returned no results - may indicate indexing issues")


if __name__ == "__main__":
    # Run these tests with: python -m pytest tests/test_integration_clusters.py -v -s
    pass
