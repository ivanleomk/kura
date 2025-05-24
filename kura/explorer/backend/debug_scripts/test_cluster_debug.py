"""Debug script to check cluster-conversation relationships."""

import os
import sys
from pathlib import Path
from sqlmodel import Session, select, func
from sqlalchemy.orm import selectinload

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from kura.explorer.api import KuraExplorer
from kura.explorer.db.models import ClusterDB, ConversationDB, ClusterConversationLink, SummaryDB

# Get checkpoint directory from environment or use default
checkpoint_dir = os.environ.get("KURA_CHECKPOINT_DIR", "/Users/jasonliu/dev/kura/tutorial_checkpoints")
print(f"Using checkpoint directory: {checkpoint_dir}")

# Initialize explorer
try:
    explorer = KuraExplorer(checkpoint_dir)
    print("Explorer initialized successfully")
except Exception as e:
    print(f"Error initializing explorer: {e}")
    sys.exit(1)

# Check cluster-conversation relationships
with Session(explorer.engine) as session:
    # First, list all clusters
    all_clusters = session.exec(select(ClusterDB).limit(10)).all()
    print("\nAvailable clusters:")
    for c in all_clusters:
        print(f"- {c.id}: {c.name}")
    
    # Get a specific cluster
    cluster_id = "a2b1f7456294467497d292b55def0b27"  # The actual ID for "Assist with data analysis and debugging in APIs"
    
    # Get cluster info
    cluster = session.exec(
        select(ClusterDB).where(ClusterDB.id == cluster_id)
    ).first()
    
    if cluster:
        print(f"\nCluster: {cluster.name}")
        print(f"Description: {cluster.description}")
        print(f"Chat IDs in JSON field: {cluster.chat_ids}")
        print(f"Number of chat IDs: {len(cluster.chat_ids) if cluster.chat_ids else 0}")
        
        # Get conversations through relationship
        cluster_with_convs = session.exec(
            select(ClusterDB)
            .options(selectinload(ClusterDB.conversations))
            .where(ClusterDB.id == cluster_id)
        ).first()
        
        print(f"\nConversations through relationship: {len(cluster_with_convs.conversations)}")
        
        # Check the link table directly
        links = session.exec(
            select(ClusterConversationLink)
            .where(ClusterConversationLink.cluster_id == cluster_id)
        ).all()
        print(f"Links in join table: {len(links)}")
        
        # Check if conversations exist
        missing_convs = []
        for chat_id in (cluster.chat_ids or []):
            conv = session.exec(
                select(ConversationDB).where(ConversationDB.chat_id == chat_id)
            ).first()
            if not conv:
                missing_convs.append(chat_id)
        
        if missing_convs:
            print(f"\nMissing conversations: {missing_convs}")
        
        # Get summaries for the conversations through relationship
        print("\nConversation summaries (from relationship):")
        for i, conv in enumerate(cluster_with_convs.conversations[:10]):  # First 10
            summary = session.exec(
                select(SummaryDB).where(SummaryDB.chat_id == conv.chat_id)
            ).first()
            if summary:
                print(f"\n{i+1}. {conv.chat_id}")
                print(f"   Request: {summary.request}")
                print(f"   Summary: {summary.summary}")
                print(f"   Task: {summary.task}")
                print(f"   Languages: {summary.languages}")