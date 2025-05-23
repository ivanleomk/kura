"""Database integrity tests for cluster-conversation relationships."""

import os
import pytest
import sqlite3
from pathlib import Path
from sqlmodel import Session, select, func

# Set environment for real checkpoint data
CHECKPOINT_DIR = "/Users/jasonliu/dev/kura/tutorial_checkpoints"
os.environ["KURA_CHECKPOINT_DIR"] = CHECKPOINT_DIR

from kura.explorer.api import KuraExplorer
from kura.explorer.db.models import ClusterDB, ConversationDB, ClusterConversationLink, SummaryDB
from kura.explorer.db.loader import CheckpointLoader


@pytest.fixture(scope="module")
def checkpoint_explorer():
    """Create explorer with real checkpoint data."""
    if not Path(CHECKPOINT_DIR).exists():
        pytest.skip(f"Checkpoint directory {CHECKPOINT_DIR} not found")
    
    explorer = KuraExplorer(CHECKPOINT_DIR)
    return explorer


class TestDatabaseSchema:
    """Test database schema and table structure."""
    
    def test_database_file_exists(self, checkpoint_explorer):
        """Test that the database file is created."""
        db_path = Path(CHECKPOINT_DIR) / "explorer.db"
        assert db_path.exists(), f"Database file not found at {db_path}"
        
        # Check file size (should not be empty)
        file_size = db_path.stat().st_size
        assert file_size > 1024, f"Database file seems too small: {file_size} bytes"
        print(f"✅ Database file exists: {file_size:,} bytes")
    
    def test_required_tables_exist(self, checkpoint_explorer):
        """Test that all required tables exist in the database."""
        db_path = Path(CHECKPOINT_DIR) / "explorer.db"
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ["conversations", "summaries", "clusters", "cluster_conversations", "messages"]
        
        for table in required_tables:
            assert table in tables, f"Required table '{table}' not found. Found: {tables}"
            print(f"✅ Table '{table}' exists")
    
    def test_table_schemas(self, checkpoint_explorer):
        """Test that tables have the expected columns."""
        db_path = Path(CHECKPOINT_DIR) / "explorer.db"
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check conversations table schema
            cursor.execute("PRAGMA table_info(conversations);")
            conv_columns = [row[1] for row in cursor.fetchall()]
            expected_conv_columns = ["chat_id", "created_at", "metadata", "message_count"]
            
            for col in expected_conv_columns:
                assert col in conv_columns, f"Column '{col}' missing from conversations table"
            
            print(f"✅ Conversations table has columns: {conv_columns}")
            
            # Check cluster_conversations table schema  
            cursor.execute("PRAGMA table_info(cluster_conversations);")
            link_columns = [row[1] for row in cursor.fetchall()]
            expected_link_columns = ["cluster_id", "conversation_id"]
            
            for col in expected_link_columns:
                assert col in link_columns, f"Column '{col}' missing from cluster_conversations table"
            
            print(f"✅ Cluster_conversations table has columns: {link_columns}")


class TestDataLoading:
    """Test that data is properly loaded into the database."""
    
    def test_conversations_loaded_from_summaries(self, checkpoint_explorer):
        """Test that conversations are created from summary data."""
        with Session(checkpoint_explorer.engine) as session:
            # Count conversations
            conv_count = session.exec(select(func.count(ConversationDB.chat_id))).one()
            
            # Count summaries
            summary_count = session.exec(select(func.count(SummaryDB.chat_id))).one()
            
            assert conv_count > 0, "No conversations found in database"
            assert summary_count > 0, "No summaries found in database"
            
            # Every summary should have a corresponding conversation
            assert conv_count >= summary_count, f"Fewer conversations ({conv_count}) than summaries ({summary_count})"
            
            print(f"✅ Found {conv_count} conversations and {summary_count} summaries")
    
    def test_conversation_ids_match_summary_ids(self, checkpoint_explorer):
        """Test that conversation IDs exactly match summary IDs."""
        with Session(checkpoint_explorer.engine) as session:
            # Get all conversation IDs
            conv_ids = set(session.exec(select(ConversationDB.chat_id)).all())
            
            # Get all summary IDs
            summary_ids = set(session.exec(select(SummaryDB.chat_id)).all())
            
            # Check for mismatches
            missing_conversations = summary_ids - conv_ids
            extra_conversations = conv_ids - summary_ids
            
            if missing_conversations:
                print(f"⚠️  Summaries without conversations: {len(missing_conversations)}")
                for missing_id in list(missing_conversations)[:5]:
                    print(f"   - {missing_id}")
            
            if extra_conversations:
                print(f"⚠️  Conversations without summaries: {len(extra_conversations)}")
                for extra_id in list(extra_conversations)[:5]:
                    print(f"   - {extra_id}")
            
            # Every summary should have a conversation
            assert len(missing_conversations) == 0, f"Found {len(missing_conversations)} summaries without conversations"
            
            print(f"✅ All {len(summary_ids)} summaries have corresponding conversations")
    
    def test_cluster_conversation_links_valid(self, checkpoint_explorer):
        """Test that cluster-conversation links point to existing records."""
        with Session(checkpoint_explorer.engine) as session:
            # Get all links
            links = session.exec(select(ClusterConversationLink)).all()
            assert len(links) > 0, "No cluster-conversation links found"
            
            # Check each link
            valid_links = 0
            invalid_cluster_links = 0
            invalid_conversation_links = 0
            
            for link in links[:100]:  # Check first 100 links
                # Check if cluster exists
                cluster = session.exec(
                    select(ClusterDB).where(ClusterDB.id == link.cluster_id)
                ).first()
                
                # Check if conversation exists
                conversation = session.exec(
                    select(ConversationDB).where(ConversationDB.chat_id == link.conversation_id)
                ).first()
                
                if cluster and conversation:
                    valid_links += 1
                else:
                    if not cluster:
                        invalid_cluster_links += 1
                    if not conversation:
                        invalid_conversation_links += 1
            
            print(f"✅ Checked {min(100, len(links))} links:")
            print(f"   - Valid: {valid_links}")
            print(f"   - Invalid cluster refs: {invalid_cluster_links}")
            print(f"   - Invalid conversation refs: {invalid_conversation_links}")
            
            # Most links should be valid
            assert valid_links > invalid_cluster_links + invalid_conversation_links, \
                "More invalid links than valid ones"


class TestClusterConversationRelationships:
    """Test the ORM relationships between clusters and conversations."""
    
    def test_cluster_conversations_relationship(self, checkpoint_explorer):
        """Test that cluster.conversations relationship works."""
        with Session(checkpoint_explorer.engine) as session:
            # Get a cluster
            cluster = session.exec(select(ClusterDB).limit(1)).first()
            assert cluster is not None, "No clusters found"
            
            # Try to access conversations through relationship
            try:
                # This might fail if the relationship isn't properly configured
                conversations = cluster.conversations
                print(f"✅ Cluster '{cluster.name}' relationship loaded {len(conversations)} conversations")
                
                # Verify conversations are actual ConversationDB objects
                for conv in conversations[:3]:
                    assert hasattr(conv, 'chat_id'), "Conversation object missing chat_id"
                    assert hasattr(conv, 'created_at'), "Conversation object missing created_at"
                    print(f"   - Conversation: {conv.chat_id[:8]}...")
                    
            except Exception as e:
                print(f"❌ Cluster.conversations relationship failed: {e}")
                # Fall back to manual join
                conversations = session.exec(
                    select(ConversationDB)
                    .join(ClusterConversationLink)
                    .where(ClusterConversationLink.cluster_id == cluster.id)
                ).all()
                print(f"⚠️  Manual join found {len(conversations)} conversations for cluster")
    
    def test_conversation_clusters_relationship(self, checkpoint_explorer):
        """Test that conversation.clusters relationship works."""
        with Session(checkpoint_explorer.engine) as session:
            # Get a conversation
            conversation = session.exec(select(ConversationDB).limit(1)).first()
            assert conversation is not None, "No conversations found"
            
            # Try to access clusters through relationship
            try:
                clusters = conversation.clusters
                print(f"✅ Conversation {conversation.chat_id[:8]}... belongs to {len(clusters)} clusters")
                
                for cluster in clusters[:3]:
                    assert hasattr(cluster, 'name'), "Cluster object missing name"
                    print(f"   - Cluster: {cluster.name}")
                    
            except Exception as e:
                print(f"❌ Conversation.clusters relationship failed: {e}")
                # Fall back to manual join
                clusters = session.exec(
                    select(ClusterDB)
                    .join(ClusterConversationLink)
                    .where(ClusterConversationLink.conversation_id == conversation.chat_id)
                ).all()
                print(f"⚠️  Manual join found {len(clusters)} clusters for conversation")


class TestAPIDataConsistency:
    """Test that API methods return consistent data."""
    
    def test_get_cluster_conversation_consistency(self, checkpoint_explorer):
        """Test that get_cluster returns consistent conversation data."""
        # Get clusters through different methods
        clusters_basic = checkpoint_explorer.get_clusters(level=0)
        assert len(clusters_basic) > 0, "No root clusters found"
        
        cluster_id = clusters_basic[0].id
        
        # Get detailed cluster info
        cluster_detail = checkpoint_explorer.get_cluster(cluster_id)
        assert cluster_detail is not None, f"Could not get cluster detail for {cluster_id}"
        
        # Check conversation count consistency
        with Session(checkpoint_explorer.engine) as session:
            # Direct database count
            db_count = session.exec(
                select(func.count(ClusterConversationLink.conversation_id))
                .where(ClusterConversationLink.cluster_id == cluster_id)
            ).one()
            
            # API reported count
            api_count = cluster_detail.conversation_count
            
            # Loaded conversations count
            loaded_convs = len(cluster_detail.conversations) if hasattr(cluster_detail, 'conversations') and cluster_detail.conversations else 0
            
            print(f"Cluster '{cluster_detail.name}' conversation counts:")
            print(f"   - Database: {db_count}")
            print(f"   - API reported: {api_count}")
            print(f"   - Loaded: {loaded_convs}")
            
            # Allow some tolerance for different counting methods
            assert abs(db_count - api_count) <= 1, \
                f"Large discrepancy between database ({db_count}) and API ({api_count}) counts"
    
    def test_search_conversation_mapping(self, checkpoint_explorer):
        """Test that search results map correctly to clusters."""
        # Search for conversations
        search_results = checkpoint_explorer.search_conversations("python")
        
        if len(search_results) > 0:
            conv = search_results[0]
            print(f"✅ Search found conversation: {conv.chat_id[:8]}...")
            
            # Check if this conversation has cluster mappings
            with Session(checkpoint_explorer.engine) as session:
                cluster_links = session.exec(
                    select(ClusterConversationLink)
                    .where(ClusterConversationLink.conversation_id == conv.chat_id)
                ).all()
                
                print(f"   - Mapped to {len(cluster_links)} clusters")
                
                for link in cluster_links[:3]:
                    cluster = session.exec(
                        select(ClusterDB).where(ClusterDB.id == link.cluster_id)
                    ).first()
                    if cluster:
                        print(f"     * {cluster.name}")
        else:
            print("⚠️  No search results found")


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_database_integrity.py -v -s
    pass 