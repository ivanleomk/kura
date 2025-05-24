"""SQLModel models for Kura Explorer database."""

from typing import List, Optional
from datetime import datetime
from sqlmodel import (
    Field,
    SQLModel,
    Session,
    Relationship,
    create_engine,
    Column,
    DateTime,
    JSON,
)


# Link table for many-to-many relationship
class ClusterConversationLink(SQLModel, table=True):
    __tablename__ = "cluster_conversations"

    cluster_id: str = Field(foreign_key="clusters.id", primary_key=True)
    conversation_id: str = Field(foreign_key="conversations.chat_id", primary_key=True)


class MessageDB(SQLModel, table=True):
    __tablename__ = "messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: str = Field(foreign_key="conversations.chat_id")
    created_at: datetime = Field(sa_column=Column(DateTime))
    role: str
    content: str

    # Relationship
    conversation: Optional["ConversationDB"] = Relationship(back_populates="messages")


class ConversationDB(SQLModel, table=True):
    __tablename__ = "conversations"

    # Override chat_id to be primary key
    chat_id: str = Field(primary_key=True)
    created_at: datetime = Field(sa_column=Column(DateTime))
    metadata_json: dict = Field(
        default_factory=dict, sa_column=Column("metadata", JSON)
    )
    message_count: int = Field(default=0)

    # Relationships
    messages: List[MessageDB] = Relationship(back_populates="conversation")
    summary: Optional["SummaryDB"] = Relationship(back_populates="conversation")
    clusters: List["ClusterDB"] = Relationship(
        back_populates="conversations", link_model=ClusterConversationLink
    )


class SummaryDB(SQLModel, table=True):
    __tablename__ = "summaries"

    # Primary key with foreign key
    chat_id: str = Field(primary_key=True, foreign_key="conversations.chat_id")

    # Fields from ConversationSummary
    summary: str
    request: Optional[str] = None
    languages: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    task: Optional[str] = None
    concerning_score: Optional[int] = None
    user_frustration: Optional[int] = None
    assistant_errors: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    metadata_json: dict = Field(
        default_factory=dict, sa_column=Column("metadata", JSON)
    )

    # Relationship
    conversation: Optional[ConversationDB] = Relationship(back_populates="summary")


class ClusterDB(SQLModel, table=True):
    __tablename__ = "clusters"

    # Primary key
    id: str = Field(primary_key=True)

    # Fields from Cluster
    name: str
    description: str
    chat_ids: List[str] = Field(default_factory=list, sa_column=Column(JSON))

    # Add self-referential foreign key
    parent_id: Optional[str] = Field(default=None, foreign_key="clusters.id")

    # Fields from ProjectedCluster
    x_coord: Optional[float] = Field(default=None)
    y_coord: Optional[float] = Field(default=None)
    level: int = Field(default=0)

    # Relationships
    parent: Optional["ClusterDB"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "ClusterDB.id"},
    )
    children: List["ClusterDB"] = Relationship(back_populates="parent")
    conversations: List[ConversationDB] = Relationship(
        back_populates="clusters", link_model=ClusterConversationLink
    )


def create_database(db_path: str):
    """Create database and tables."""
    engine = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(engine)
    return engine


def get_session(engine) -> Session:
    """Get database session."""
    return Session(engine)
