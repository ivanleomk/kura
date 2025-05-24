"""Load Kura checkpoint data into SQLite database."""

import os
import json
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path

from sqlmodel import Session, select
from tqdm import tqdm

from .models import (
    create_database, get_session,
    ConversationDB,
    MessageDB,
    SummaryDB,
    ClusterDB,
    ClusterConversationLink
)
from kura.types import Conversation, ConversationSummary, Cluster
from kura.types.dimensionality import ProjectedCluster


class CheckpointLoader:
    """Load checkpoint data into SQLite database."""
    
    def __init__(self, checkpoint_dir: str, db_path: str = None):
        self.checkpoint_dir = Path(checkpoint_dir)
        if db_path is None:
            db_path = self.checkpoint_dir / "explorer.db"
        self.db_path = db_path
        self.engine = create_database(str(db_path))
        self.session = get_session(self.engine)
        
    def load_all(self) -> None:
        """Load all checkpoint data into database."""
        print("Loading checkpoint data into SQLite database...")
        
        # Load conversations if available
        conv_file = self.checkpoint_dir / "conversations.json"
        if conv_file.exists():
            self.load_conversations(str(conv_file))
            
        # Load summaries
        self.load_summaries()
        
        # Load clusters and dimensionality
        self.load_clusters()
        
        print("Data loading complete!")
        
    def load_conversations(self, file_path: str) -> None:
        """Load conversations from JSON dump."""
        print(f"Loading conversations from {file_path}...")
        
        conversations = Conversation.from_conversation_dump(file_path)
        
        for conv in tqdm(conversations, desc="Loading conversations"):
            # Create conversation record
            conv_db = ConversationDB(
                chat_id=conv.chat_id,
                created_at=conv.created_at,
                metadata_json=conv.metadata,
                message_count=len(conv.messages)
            )
            self.session.add(conv_db)
            
            # Create message records
            for msg in conv.messages:
                msg_db = MessageDB(
                    conversation_id=conv.chat_id,
                    created_at=msg.created_at,
                    role=msg.role,
                    content=msg.content
                )
                self.session.add(msg_db)
                
        self.session.commit()
        
    def load_summaries(self) -> None:
        """Load summaries from checkpoint."""
        summary_file = self.checkpoint_dir / "summaries.jsonl"
        if not summary_file.exists():
            print("No summaries.jsonl found, skipping...")
            return
            
        print(f"Loading summaries from {summary_file}...")
        
        with open(summary_file, 'r') as f:
            for line in tqdm(f, desc="Loading summaries"):
                summary_data = ConversationSummary.model_validate_json(line)
                
                # Create a stub conversation record if it doesn't exist
                existing_conv = self.session.exec(
                    select(ConversationDB).where(ConversationDB.chat_id == summary_data.chat_id)
                ).first()
                
                if not existing_conv:
                    # Create a minimal conversation record from summary data
                    # Use a default created_at if not available
                    created_at = getattr(summary_data, 'created_at', None)
                    if not created_at:
                        # Try to get from metadata or use epoch
                        created_at = datetime.fromtimestamp(0)  # Default to epoch
                    
                    conv_db = ConversationDB(
                        chat_id=summary_data.chat_id,
                        created_at=created_at,
                        metadata_json={},
                        message_count=0  # We don't have message data
                    )
                    self.session.add(conv_db)
                
                summary_db = SummaryDB(
                    chat_id=summary_data.chat_id,
                    summary=summary_data.summary,
                    request=summary_data.request,
                    languages=summary_data.languages,
                    task=summary_data.task,
                    concerning_score=summary_data.concerning_score,
                    user_frustration=summary_data.user_frustration,
                    assistant_errors=summary_data.assistant_errors,
                    metadata_json=summary_data.metadata
                )
                self.session.add(summary_db)
                
        self.session.commit()
        
    def load_clusters(self) -> None:
        """Load clusters and dimensionality data."""
        # First load base clusters
        clusters_file = self.checkpoint_dir / "clusters.jsonl"
        meta_clusters_file = self.checkpoint_dir / "meta_clusters.jsonl"
        dimensionality_file = self.checkpoint_dir / "dimensionality.jsonl"
        
        all_clusters: Dict[str, Cluster] = {}
        cluster_to_conversations: Dict[str, List[str]] = {}
        
        # Load base clusters
        if clusters_file.exists():
            print(f"Loading clusters from {clusters_file}...")
            with open(clusters_file, 'r') as f:
                for line in tqdm(f, desc="Loading base clusters"):
                    cluster = Cluster.model_validate_json(line)
                    all_clusters[cluster.id] = cluster
                    cluster_to_conversations[cluster.id] = cluster.chat_ids
                    
        # Load meta clusters
        if meta_clusters_file.exists():
            print(f"Loading meta clusters from {meta_clusters_file}...")
            with open(meta_clusters_file, 'r') as f:
                for line in tqdm(f, desc="Loading meta clusters"):
                    cluster = Cluster.model_validate_json(line)
                    all_clusters[cluster.id] = cluster
                    cluster_to_conversations[cluster.id] = cluster.chat_ids
                    
        # Load dimensionality data and merge
        dimensionality_data: Dict[str, ProjectedCluster] = {}
        if dimensionality_file.exists():
            print(f"Loading dimensionality data from {dimensionality_file}...")
            with open(dimensionality_file, 'r') as f:
                for line in tqdm(f, desc="Loading dimensionality"):
                    proj_cluster = ProjectedCluster.model_validate_json(line)
                    dimensionality_data[proj_cluster.id] = proj_cluster
                    
        # Create cluster records
        print("Creating cluster records...")
        for cluster_id, cluster in tqdm(all_clusters.items(), desc="Creating clusters"):
            # Get dimensionality data if available
            proj_data = dimensionality_data.get(cluster_id)
            
            cluster_db = ClusterDB(
                id=cluster.id,
                name=cluster.name,
                description=cluster.description,
                chat_ids=cluster.chat_ids,  # Preserve original chat_ids for compatibility
                parent_id=cluster.parent_id,
                level=proj_data.level if proj_data else 0,
                x_coord=proj_data.x_coord if proj_data else None,
                y_coord=proj_data.y_coord if proj_data else None
            )
            self.session.add(cluster_db)
            
        self.session.commit()
        
        # Create cluster-conversation associations
        print("Creating cluster-conversation associations...")
        for cluster_id, conv_ids in tqdm(cluster_to_conversations.items(), 
                                        desc="Creating associations"):
            for conv_id in conv_ids:
                link = ClusterConversationLink(
                    cluster_id=cluster_id,
                    conversation_id=conv_id
                )
                self.session.add(link)
                
        self.session.commit()
        
    def close(self):
        """Close database session."""
        self.session.close()