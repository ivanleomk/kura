"""Core API for Kura Explorer."""

import os
from typing import List, Optional, Dict, Any
from pathlib import Path

from sqlmodel import Session, create_engine, select, func
from sqlalchemy.orm import selectinload

from .db.models import (
    ConversationDB,
    MessageDB,
    SummaryDB,
    ClusterDB,
    ClusterConversationLink,
    get_session
)
from .db.loader import CheckpointLoader
from kura.types import Conversation, ConversationSummary, Cluster


class ConversationDetail:
    """Detailed conversation with messages and summary."""
    def __init__(self, conversation: ConversationDB, messages: List[MessageDB], 
                 summary: Optional[SummaryDB] = None):
        self.id = conversation.chat_id
        self.created_at = conversation.created_at
        self.metadata = conversation.metadata_json
        self.messages = messages
        self.summary = summary
        self.clusters = conversation.clusters


class ClusterDetail:
    """Detailed cluster with conversations and hierarchy."""
    def __init__(self, cluster: ClusterDB, conversations: List[ConversationDB], 
                 children: List[ClusterDB], parent: Optional[ClusterDB] = None):
        self.id = cluster.id
        self.name = cluster.name
        self.description = cluster.description
        self.level = cluster.level
        self.x_coord = cluster.x_coord
        self.y_coord = cluster.y_coord
        self.conversations = conversations
        self.children = children
        self.parent = parent
        self.conversation_count = len(conversations)


class KuraExplorer:
    """Main API for exploring Kura checkpoint data."""
    
    def __init__(self, checkpoint_dir: str):
        """Initialize explorer with checkpoint directory."""
        self.checkpoint_dir = Path(checkpoint_dir)
        self.db_path = self.checkpoint_dir / "explorer.db"
        
        # Check if we need to load data
        if not self.db_path.exists():
            self.load_data()
            
        # Connect to database
        self.engine = create_engine(f'sqlite:///{self.db_path}')
        
    def load_data(self) -> None:
        """Load all checkpoint data into SQLite."""
        loader = CheckpointLoader(str(self.checkpoint_dir))
        loader.load_all()
        loader.close()
        
    def get_conversations(self, 
                         limit: int = 50, 
                         offset: int = 0,
                         cluster_id: Optional[str] = None,
                         search: Optional[str] = None) -> List[ConversationDB]:
        """Get conversations with pagination and filtering."""
        with Session(self.engine) as session:
            query = select(ConversationDB).options(
                selectinload(ConversationDB.clusters)
            )
            
            if cluster_id:
                query = query.join(ClusterConversationLink).join(ClusterDB).where(
                    ClusterDB.id == cluster_id
                )
                
            if search:
                # Search in summaries
                query = query.join(SummaryDB).where(
                    SummaryDB.summary.contains(search) |
                    SummaryDB.task.contains(search) |
                    SummaryDB.request.contains(search)
                )
                
            return session.exec(query.offset(offset).limit(limit)).all()
            
    def get_conversation(self, conversation_id: str) -> Optional[ConversationDetail]:
        """Get detailed conversation with messages and summary."""
        with Session(self.engine) as session:
            conv = session.exec(
                select(ConversationDB)
                .options(selectinload(ConversationDB.clusters))
                .where(ConversationDB.chat_id == conversation_id)
            ).first()
            
            if not conv:
                return None
                
            messages = session.exec(
                select(MessageDB).where(MessageDB.conversation_id == conversation_id)
                .order_by(MessageDB.created_at)
            ).all()
            
            summary = session.exec(
                select(SummaryDB).where(SummaryDB.chat_id == conversation_id)
            ).first()
            
            return ConversationDetail(conv, messages, summary)
            
    def get_clusters(self, 
                    parent_id: Optional[str] = None,
                    level: Optional[int] = None) -> List[ClusterDB]:
        """Get clusters, optionally filtered by parent or level."""
        with Session(self.engine) as session:
            query = select(ClusterDB)
            
            if parent_id is not None:
                query = query.where(ClusterDB.parent_id == parent_id)
            elif level is not None:
                query = query.where(ClusterDB.level == level)
            else:
                # Default to root clusters
                query = query.where(ClusterDB.parent_id == None)
                
            results = session.exec(query.order_by(ClusterDB.name)).all()
            
            # Note: Do not access relationships here as they will be detached
            # The router code should handle conversation counting separately
                
            return list(results)
            
    def get_cluster(self, cluster_id: str) -> Optional[ClusterDetail]:
        """Get cluster details with conversations and children."""
        with Session(self.engine) as session:
            cluster = session.exec(
                select(ClusterDB)
                .options(selectinload(ClusterDB.conversations))
                .where(ClusterDB.id == cluster_id)
            ).first()
            
            if not cluster:
                return None
                
            conversations = cluster.conversations
            children = session.exec(
                select(ClusterDB).where(ClusterDB.parent_id == cluster_id)
            ).all()
            
            parent = None
            if cluster.parent_id:
                parent = session.exec(
                    select(ClusterDB).where(ClusterDB.id == cluster.parent_id)
                ).first()
                
            return ClusterDetail(cluster, conversations, children, parent)
            
    def get_cluster_hierarchy(self, cluster_id: str) -> List[ClusterDB]:
        """Get full hierarchy path from root to specified cluster."""
        hierarchy = []
        
        with Session(self.engine) as session:
            current = session.exec(
                select(ClusterDB).where(ClusterDB.id == cluster_id)
            ).first()
            
            while current:
                hierarchy.insert(0, current)
                if current.parent_id:
                    current = session.exec(
                        select(ClusterDB).where(ClusterDB.id == current.parent_id)
                    ).first()
                else:
                    break
                    
        return hierarchy
        
    def search_conversations(self, query: str) -> List[ConversationDB]:
        """Full-text search across conversations."""
        with Session(self.engine) as session:
            # Search in messages
            msg_query = select(ConversationDB).distinct().join(MessageDB).where(
                MessageDB.content.contains(query)
            ).options(selectinload(ConversationDB.clusters))
            
            # Search in summaries
            summary_query = select(ConversationDB).join(SummaryDB).where(
                SummaryDB.summary.contains(query) |
                SummaryDB.task.contains(query) |
                SummaryDB.request.contains(query)
            ).options(selectinload(ConversationDB.clusters))
            
            # Get results from both queries
            msg_results = session.exec(msg_query).all()
            summary_results = session.exec(summary_query).all()
            
            # Combine and deduplicate
            all_results = {conv.chat_id: conv for conv in msg_results}
            for conv in summary_results:
                all_results[conv.chat_id] = conv
                
            return list(all_results.values())
            
    def get_summary(self, chat_id: str) -> Optional[SummaryDB]:
        """Get summary for a specific conversation."""
        with Session(self.engine) as session:
            return session.exec(
                select(SummaryDB).where(SummaryDB.chat_id == chat_id)
            ).first()
            
    def get_stats(self) -> Dict[str, Any]:
        """Get overall statistics about the checkpoint data."""
        with Session(self.engine) as session:
            stats = {
                'total_conversations': session.exec(select(func.count(ConversationDB.chat_id))).one(),
                'total_messages': session.exec(select(func.count(MessageDB.id))).one(),
                'total_summaries': session.exec(select(func.count(SummaryDB.chat_id))).one(),
                'total_clusters': session.exec(select(func.count(ClusterDB.id))).one(),
                'root_clusters': session.exec(
                    select(func.count(ClusterDB.id)).where(ClusterDB.parent_id == None)
                ).one(),
                'max_cluster_level': session.exec(select(func.max(ClusterDB.level))).one() or 0
            }
            return stats