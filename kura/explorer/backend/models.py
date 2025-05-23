"""Pydantic models for API responses."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    """Message in a conversation."""
    id: int
    conversation_id: str
    created_at: datetime
    role: str
    content: str


class SummaryResponse(BaseModel):
    """Conversation summary."""
    chat_id: str
    summary: str
    request: Optional[str] = None
    languages: Optional[List[str]] = None
    task: Optional[str] = None
    concerning_score: Optional[int] = None
    user_frustration: Optional[int] = None
    assistant_errors: Optional[List[str]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationResponse(BaseModel):
    """Basic conversation info."""
    id: str
    created_at: datetime
    metadata: Dict[str, Any]
    message_count: int
    summary: Optional[SummaryResponse] = None
    cluster_names: List[str] = Field(default_factory=list)


class ConversationDetailResponse(BaseModel):
    """Detailed conversation with messages."""
    id: str
    created_at: datetime
    metadata: Dict[str, Any]
    messages: List[MessageResponse]
    summary: Optional[SummaryResponse] = None
    clusters: List[str] = Field(default_factory=list)


class ClusterResponse(BaseModel):
    """Basic cluster info."""
    id: str
    name: str
    description: str
    level: int
    parent_id: Optional[str] = None
    x_coord: Optional[float] = None
    y_coord: Optional[float] = None
    conversation_count: int = 0
    child_count: int = 0
    avg_frustration: Optional[float] = None
    languages: List[str] = Field(default_factory=list)


class ClusterDetailResponse(BaseModel):
    """Detailed cluster info."""
    id: str
    name: str
    description: str
    level: int
    parent_id: Optional[str] = None
    x_coord: Optional[float] = None
    y_coord: Optional[float] = None
    conversation_count: int
    avg_frustration: Optional[float] = None
    languages: List[str] = Field(default_factory=list)
    parent: Optional[ClusterResponse] = None
    children: List[ClusterResponse] = Field(default_factory=list)
    conversations: List[ConversationResponse] = Field(default_factory=list)
    hierarchy: List[ClusterResponse] = Field(default_factory=list)


class ClusterTreeNode(BaseModel):
    """Tree node for hierarchical view."""
    id: str
    name: str
    description: str
    level: int
    conversation_count: int
    avg_frustration: Optional[float] = None
    children: List['ClusterTreeNode'] = Field(default_factory=list)


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    items: List[Any]
    total: int
    limit: int
    offset: int
    has_more: bool


class SearchResult(BaseModel):
    """Search results."""
    conversations: List[ConversationResponse]
    total_count: int
    query: str


class StatsResponse(BaseModel):
    """Overall statistics."""
    total_conversations: int
    total_messages: int
    total_summaries: int
    total_clusters: int
    root_clusters: int
    max_cluster_level: int


class LanguageStats(BaseModel):
    """Language distribution statistics."""
    language: str
    count: int
    percentage: float


class MetadataDistribution(BaseModel):
    """Metadata value distribution."""
    key: str
    values: Dict[str, int]


class FrustrationMapItem(BaseModel):
    """Frustration score mapping."""
    cluster_id: str
    cluster_name: str
    avg_frustration: float
    conversation_count: int
    x_coord: Optional[float] = None
    y_coord: Optional[float] = None


class ThemeInsight(BaseModel):
    """Common theme across clusters."""
    theme: str
    cluster_ids: List[str]
    frequency: int
    example_summaries: List[str]


class PatternInsight(BaseModel):
    """Common conversation pattern."""
    pattern_name: str
    description: str
    frequency: int
    avg_length: float
    example_conversation_ids: List[str]


# Update forward references
ClusterTreeNode.model_rebuild()