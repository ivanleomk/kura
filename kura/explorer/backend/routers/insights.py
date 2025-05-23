"""Insights and analysis API router."""

from typing import List, Dict, Any, Optional
from collections import Counter, defaultdict
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlmodel import Session, select, func
from pydantic import BaseModel

from ..models import (
    LanguageStats, MetadataDistribution, FrustrationMapItem,
    ThemeInsight, PatternInsight
)
from ...api import KuraExplorer
from ...db.models import SummaryDB, ClusterDB, ConversationDB, ClusterConversationLink


router = APIRouter()


def get_explorer() -> KuraExplorer:
    """Dependency to get explorer instance."""
    from ..main import explorer
    if not explorer:
        raise HTTPException(status_code=503, detail="Explorer not initialized")
    return explorer


@router.get("/language-stats", response_model=List[LanguageStats])
async def get_language_statistics(
    explorer: KuraExplorer = Depends(get_explorer)
):
    """Get language usage statistics across all conversations."""
    with Session(explorer.engine) as session:
        summaries = session.exec(select(SummaryDB)).all()
    
    # Count languages
    language_counts = Counter()
    total_with_languages = 0
    
    for summary in summaries:
        if summary.languages:
            total_with_languages += 1
            for lang in summary.languages:
                language_counts[lang] += 1
    
    # Convert to response
    stats = []
    for lang, count in language_counts.most_common():
        stats.append(LanguageStats(
            language=lang,
            count=count,
            percentage=round((count / total_with_languages) * 100, 2) if total_with_languages > 0 else 0
        ))
    
    return stats


@router.get("/frustration-map", response_model=List[FrustrationMapItem])
async def get_frustration_heatmap(
    min_conversations: int = Query(5, description="Minimum conversations in cluster"),
    explorer: KuraExplorer = Depends(get_explorer)
):
    """Get user frustration heatmap data for clusters."""
    with Session(explorer.engine) as session:
        clusters = session.exec(select(ClusterDB)).all()
    
    frustration_map = []
    
    for cluster in clusters:
        # Get summaries for this cluster
        with Session(explorer.engine) as session:
            stmt = select(SummaryDB).join(
                ClusterConversationLink,
                SummaryDB.chat_id == ClusterConversationLink.conversation_id
            ).where(
                ClusterConversationLink.cluster_id == cluster.id
            )
            summaries = session.exec(stmt).all()
        
        if len(summaries) < min_conversations:
            continue
        
        # Calculate average frustration
        frustration_scores = [s.user_frustration for s in summaries if s.user_frustration]
        if frustration_scores:
            avg_frustration = sum(frustration_scores) / len(frustration_scores)
            
            frustration_map.append(FrustrationMapItem(
                cluster_id=cluster.id,
                cluster_name=cluster.name,
                avg_frustration=round(avg_frustration, 2),
                conversation_count=len(summaries),
                x_coord=cluster.x_coord,
                y_coord=cluster.y_coord
            ))
    
    # Sort by frustration level
    frustration_map.sort(key=lambda x: x.avg_frustration, reverse=True)
    
    return frustration_map


class MetadataDistributionResponse(BaseModel):
    """Metadata distribution analysis response."""
    key: str
    total_conversations: int
    conversations_with_key: int
    value_distribution: Dict[str, int]
    unique_values: int


@router.get("/metadata-dist", response_model=MetadataDistributionResponse)
async def get_metadata_distribution(
    key: str = Query(..., description="Metadata key to analyze"),
    explorer: KuraExplorer = Depends(get_explorer)
):
    """Get distribution of metadata values."""
    with Session(explorer.engine) as session:
        conversations = session.exec(select(ConversationDB)).all()
    
    value_counts = Counter()
    total_with_key = 0
    
    for conv in conversations:
        if conv.metadata_json and key in conv.metadata_json:
            total_with_key += 1
            value = conv.metadata_json[key]
            # Convert lists to strings for counting
            if isinstance(value, list):
                value = str(value)
            value_counts[str(value)] += 1
    
    return MetadataDistributionResponse(
        key=key,
        total_conversations=len(conversations),
        conversations_with_key=total_with_key,
        value_distribution=dict(value_counts.most_common(50)),  # Top 50 values
        unique_values=len(value_counts)
    )


@router.get("/themes", response_model=List[ThemeInsight])
async def get_common_themes(
    min_frequency: int = Query(3, description="Minimum frequency for theme"),
    explorer: KuraExplorer = Depends(get_explorer)
):
    """Extract common themes across clusters."""
    # This is a simplified version - in production, you'd use NLP
    # to extract actual themes from summaries
    
    with Session(explorer.engine) as session:
        clusters = session.exec(select(ClusterDB)).all()
    
    # Group clusters by similar names/descriptions
    theme_groups = defaultdict(list)
    
    for cluster in clusters:
        # Extract key words from cluster name (simplified)
        words = cluster.name.lower().split()
        for word in words:
            if len(word) > 4:  # Skip short words
                theme_groups[word].append(cluster)
    
    # Convert to response
    themes = []
    for theme, cluster_list in theme_groups.items():
        if len(cluster_list) >= min_frequency:
            # Get sample summaries
            sample_summaries = []
            for cluster in cluster_list[:3]:
                with Session(explorer.engine) as session:
                    stmt = select(SummaryDB).join(
                        ClusterConversationLink,
                        SummaryDB.chat_id == ClusterConversationLink.conversation_id
                    ).where(
                        ClusterConversationLink.cluster_id == cluster.id
                    ).limit(2)
                    summaries = session.exec(stmt).all()
                    sample_summaries.extend([s.summary for s in summaries])
            
            themes.append(ThemeInsight(
                theme=theme.title(),
                cluster_ids=[c.id for c in cluster_list],
                frequency=len(cluster_list),
                example_summaries=sample_summaries[:5]
            ))
    
    # Sort by frequency
    themes.sort(key=lambda x: x.frequency, reverse=True)
    
    return themes[:20]  # Top 20 themes


class OutlierResponse(BaseModel):
    """Response for outlier conversations."""
    high_frustration: List[Dict[str, Any]]
    very_short: List[Dict[str, Any]]
    multilingual: List[Dict[str, Any]]
    assistant_errors: List[Dict[str, Any]]


@router.get("/outliers", response_model=OutlierResponse)
async def get_outlier_conversations(
    limit: int = Query(20, ge=1, le=100),
    explorer: KuraExplorer = Depends(get_explorer)
):
    """Find conversations that don't fit typical patterns."""
    with Session(explorer.engine) as session:
        # Get conversations with extreme characteristics
        
        # Very high frustration
        high_frustration = session.exec(
            select(ConversationDB).join(SummaryDB).where(
                SummaryDB.user_frustration == 5
            ).limit(limit // 4)
        ).all()
        
        # Very short conversations
        short_convs = session.exec(
            select(ConversationDB).where(
                ConversationDB.message_count <= 2
            ).limit(limit // 4)
        ).all()
        
        # Unusual language combinations - filter in Python since SQLite JSON functions vary
        all_summaries = session.exec(select(SummaryDB)).all()
        multilang_summaries = [
            s for s in all_summaries 
            if s.languages and len(s.languages) >= 3
        ][:limit // 4]
        
        # Conversations with errors
        error_summaries = session.exec(
            select(SummaryDB).where(
                SummaryDB.assistant_errors != None
            ).limit(limit // 4)
        ).all()
    
    return OutlierResponse(
        high_frustration=[
            {
                "conversation_id": conv.chat_id,
                "message_count": conv.message_count,
                "reason": "Very high user frustration (5/5)"
            } for conv in high_frustration
        ],
        very_short=[
            {
                "conversation_id": conv.chat_id,
                "message_count": conv.message_count,
                "reason": f"Only {conv.message_count} messages"
            } for conv in short_convs
        ],
        multilingual=[
            {
                "conversation_id": summary.chat_id,
                "languages": summary.languages,
                "reason": f"Multiple languages: {', '.join(summary.languages)}"
            } for summary in multilang_summaries
        ],
        assistant_errors=[
            {
                "conversation_id": summary.chat_id,
                "errors": summary.assistant_errors,
                "reason": "Assistant made errors"
            } for summary in error_summaries
        ]
    )


class CommonPatternsResponse(BaseModel):
    """Response for common conversation patterns."""
    conversation_length_distribution: List[Dict[str, int]]
    common_tasks: List[Dict[str, Any]]
    average_conversation_length: float


@router.get("/common-patterns", response_model=CommonPatternsResponse)
async def get_common_patterns(
    explorer: KuraExplorer = Depends(get_explorer)
):
    """Identify common conversation patterns."""
    with Session(explorer.engine) as session:
        # Get conversation lengths distribution
        length_dist = session.exec(
            select(
                ConversationDB.message_count,
                func.count(ConversationDB.chat_id).label('count')
            ).group_by(ConversationDB.message_count)
        ).all()
        
        # Get task distribution
        task_counts = session.exec(
            select(
                SummaryDB.task,
                func.count(SummaryDB.chat_id).label('count')
            ).where(SummaryDB.task != None).group_by(SummaryDB.task)
        ).all()
    
    # Analyze patterns
    avg_length = sum(l[0] * l[1] for l in length_dist) / sum(l[1] for l in length_dist) if length_dist else 0
    
    return CommonPatternsResponse(
        conversation_length_distribution=[
            {"message_count": l[0], "frequency": l[1]} 
            for l in sorted(length_dist, key=lambda x: x[1], reverse=True)[:20]
        ],
        common_tasks=[
            {"task": t[0], "frequency": t[1]}
            for t in sorted(task_counts, key=lambda x: x[1], reverse=True)[:20]
        ],
        average_conversation_length=avg_length
    )


class ClusterComparison(BaseModel):
    """Single cluster comparison data."""
    cluster_id: str
    cluster_name: str
    conversation_count: int
    avg_frustration: Optional[float]
    top_languages: List[tuple]
    top_tasks: List[tuple]
    level: int


class CompareResponse(BaseModel):
    """Response for cluster comparison."""
    clusters: List[Dict[str, Any]]


@router.post("/compare-clusters", response_model=CompareResponse)
async def compare_clusters(
    cluster_ids: List[str],
    explorer: KuraExplorer = Depends(get_explorer)
):
    """Compare multiple clusters side by side."""
    if len(cluster_ids) < 2 or len(cluster_ids) > 5:
        raise HTTPException(status_code=400, detail="Please provide 2-5 cluster IDs")
    
    comparisons = []
    
    for cluster_id in cluster_ids:
        cluster = explorer.get_cluster(cluster_id)
        if not cluster:
            continue
        
        # Get summaries
        with Session(explorer.engine) as session:
            stmt = select(SummaryDB).join(
                ClusterConversationLink,
                SummaryDB.chat_id == ClusterConversationLink.conversation_id
            ).where(
                ClusterConversationLink.cluster_id == cluster_id
            )
            summaries = session.exec(stmt).all()
        
        # Calculate metrics
        frustration_scores = [s.user_frustration for s in summaries if s.user_frustration]
        avg_frustration = sum(frustration_scores) / len(frustration_scores) if frustration_scores else None
        
        language_counts = Counter()
        task_counts = Counter()
        
        for s in summaries:
            if s.languages:
                for lang in s.languages:
                    language_counts[lang] += 1
            if s.task:
                task_counts[s.task] += 1
        
        comparisons.append({
            "cluster_id": cluster_id,
            "cluster_name": cluster.name,
            "conversation_count": cluster.conversation_count,
            "avg_frustration": round(avg_frustration, 2) if avg_frustration else None,
            "top_languages": language_counts.most_common(5),
            "top_tasks": task_counts.most_common(5),
            "level": cluster.level
        })
    
    return CompareResponse(clusters=comparisons)