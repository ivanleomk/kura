"""Clusters API router."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlmodel import Session, select, func
from sqlalchemy.orm import selectinload

from kura.explorer.backend.models import (
    ClusterResponse, ClusterDetailResponse, ClusterTreeNode,
    PaginatedResponse, SummaryResponse, ConversationResponse
)
from kura.explorer.api import KuraExplorer
from kura.explorer.db.models import ClusterDB, SummaryDB, ClusterConversationLink, ConversationDB


router = APIRouter()


def get_explorer() -> KuraExplorer:
    """Dependency to get explorer instance."""
    try:
        # Try to import from main directly (when running with uvicorn)
        from main import explorer
    except ImportError:
        # Fallback to full path (for testing)
        from kura.explorer.backend.main import explorer
    
    if not explorer:
        raise HTTPException(status_code=503, detail="Explorer not initialized")
    return explorer


@router.get("", response_model=PaginatedResponse)
async def get_clusters(
    parent_id: Optional[str] = Query(None, description="Filter by parent cluster ID"),
    level: Optional[int] = Query(None, description="Filter by cluster level"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("name", regex="^(name|conversation_count|frustration)$"),
    sort_desc: bool = Query(False),
    language: Optional[str] = Query(None, description="Filter by language"),
    min_frustration: Optional[float] = Query(None, ge=1, le=5),
    explorer: KuraExplorer = Depends(get_explorer)
):
    """Get clusters with pagination and filtering."""
    from sqlalchemy import and_, or_
    from sqlalchemy.sql import literal_column
    
    with Session(explorer.engine) as session:
        # Build base query
        query = select(ClusterDB).options(
            selectinload(ClusterDB.conversations),
            selectinload(ClusterDB.children)
        )
        
        # Apply parent/level filters
        if parent_id is not None:
            query = query.where(ClusterDB.parent_id == parent_id)
        elif level is not None:
            query = query.where(ClusterDB.level == level)
        else:
            query = query.where(ClusterDB.parent_id == None)
        
        # Get all clusters first for filtering
        all_clusters = session.exec(query).all()
        
        # Calculate metrics and filter
        enriched_clusters = []
        
        for cluster in all_clusters:
            # Get summaries for this cluster to calculate metrics
            stmt = select(SummaryDB).join(
                ClusterConversationLink,
                SummaryDB.chat_id == ClusterConversationLink.conversation_id
            ).where(
                ClusterConversationLink.cluster_id == cluster.id
            )
            summaries = session.exec(stmt).all()
            
            # Calculate average frustration
            frustration_scores = [s.user_frustration for s in summaries if s.user_frustration]
            avg_frustration = sum(frustration_scores) / len(frustration_scores) if frustration_scores else None
            
            # Get languages
            all_languages = []
            for s in summaries:
                if s.languages:
                    all_languages.extend(s.languages)
            unique_languages = list(set(all_languages))
            
            # Apply filters
            if language and language not in unique_languages:
                continue
            if min_frustration and (not avg_frustration or avg_frustration < min_frustration):
                continue
            
            # Count children directly from loaded relationship
            child_count = len(cluster.children)
            
            enriched_clusters.append({
                "cluster": cluster,
                "avg_frustration": avg_frustration,
                "languages": unique_languages,
                "child_count": child_count
            })
        
        # Sort
        if sort_by == "name":
            enriched_clusters.sort(key=lambda x: x["cluster"].name, reverse=sort_desc)
        elif sort_by == "conversation_count":
            enriched_clusters.sort(key=lambda x: len(x["cluster"].conversations), reverse=sort_desc)
        elif sort_by == "frustration":
            enriched_clusters.sort(key=lambda x: x["avg_frustration"] or 0, reverse=sort_desc)
        
        # Paginate
        total = len(enriched_clusters)
        paginated = enriched_clusters[offset:offset + limit]
    
    # Convert to response models
    items = []
    for item in paginated:
        cluster = item["cluster"]
        items.append(ClusterResponse(
            id=cluster.id,
            name=cluster.name,
            description=cluster.description,
            level=cluster.level,
            parent_id=cluster.parent_id,
            x_coord=cluster.x_coord,
            y_coord=cluster.y_coord,
            conversation_count=len(cluster.conversations) if hasattr(cluster, 'conversations') else 0,
            child_count=item["child_count"],
            avg_frustration=item["avg_frustration"],
            languages=item["languages"]
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total
    )


@router.get("/tree", response_model=List[ClusterTreeNode])
async def get_cluster_tree(
    explorer: KuraExplorer = Depends(get_explorer)
):
    """Get the full cluster hierarchy as a tree structure."""
    root_clusters = explorer.get_clusters(level=0)
    
    def build_tree_node(cluster) -> ClusterTreeNode:
        """Recursively build tree nodes."""
        children = explorer.get_clusters(parent_id=cluster.id)
        
        # Get average frustration for this cluster
        with Session(explorer.engine) as session:
            stmt = select(SummaryDB).join(
                ClusterConversationLink,
                SummaryDB.chat_id == ClusterConversationLink.conversation_id
            ).where(
                ClusterConversationLink.cluster_id == cluster.id
            )
            summaries = session.exec(stmt).all()
        
        frustration_scores = [s.user_frustration for s in summaries if s.user_frustration]
        avg_frustration = sum(frustration_scores) / len(frustration_scores) if frustration_scores else None
        
        return ClusterTreeNode(
            id=cluster.id,
            name=cluster.name,
            description=cluster.description,
            level=cluster.level,
            conversation_count=len(cluster.conversations) if hasattr(cluster, 'conversations') else 0,
            avg_frustration=avg_frustration,
            children=[build_tree_node(child) for child in children]
        )
    
    return [build_tree_node(cluster) for cluster in root_clusters]


@router.get("/{cluster_id}", response_model=ClusterDetailResponse)
async def get_cluster(
    cluster_id: str,
    explorer: KuraExplorer = Depends(get_explorer)
):
    """Get detailed cluster information."""
    cluster_detail = explorer.get_cluster(cluster_id)
    if not cluster_detail:
        raise HTTPException(status_code=404, detail="Cluster not found")
    
    # Get summaries for metrics
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
    
    all_languages = []
    for s in summaries:
        if s.languages:
            all_languages.extend(s.languages)
    unique_languages = list(set(all_languages))
    
    # Get hierarchy
    hierarchy = explorer.get_cluster_hierarchy(cluster_id)
    
    # Get all conversations (not just samples)
    all_conversations = []
    for conv in cluster_detail.conversations:
        summary = explorer.get_summary(conv.chat_id)
        all_conversations.append(ConversationResponse(
            id=conv.chat_id,
            created_at=conv.created_at,
            metadata=conv.metadata_json or {},
            message_count=conv.message_count,
            summary=SummaryResponse(**summary.__dict__) if summary else None,
            cluster_names=[]
        ))
    
    return ClusterDetailResponse(
        id=cluster_detail.id,
        name=cluster_detail.name,
        description=cluster_detail.description,
        level=cluster_detail.level,
        parent_id=cluster_detail.parent.id if cluster_detail.parent else None,
        x_coord=cluster_detail.x_coord,
        y_coord=cluster_detail.y_coord,
        conversation_count=cluster_detail.conversation_count,
        avg_frustration=avg_frustration,
        languages=unique_languages,
        parent=ClusterResponse(
            id=cluster_detail.parent.id,
            name=cluster_detail.parent.name,
            description=cluster_detail.parent.description,
            level=cluster_detail.parent.level,
            parent_id=cluster_detail.parent.parent_id,
            x_coord=cluster_detail.parent.x_coord,
            y_coord=cluster_detail.parent.y_coord,
            conversation_count=0,
            child_count=0
        ) if cluster_detail.parent else None,
        children=[
            ClusterResponse(
                id=child.id,
                name=child.name,
                description=child.description,
                level=child.level,
                parent_id=child.parent_id,
                x_coord=child.x_coord,
                y_coord=child.y_coord,
                conversation_count=len(child.conversations) if hasattr(child, 'conversations') else 0,
                child_count=0
            ) for child in cluster_detail.children
        ],
        conversations=all_conversations,
        hierarchy=[
            ClusterResponse(
                id=h.id,
                name=h.name,
                description=h.description,
                level=h.level,
                parent_id=h.parent_id,
                x_coord=h.x_coord,
                y_coord=h.y_coord,
                conversation_count=0,
                child_count=0
            ) for h in hierarchy
        ]
    )


@router.get("/{cluster_id}/summary")
async def get_cluster_summary(
    cluster_id: str,
    explorer: KuraExplorer = Depends(get_explorer)
):
    """Get aggregated summary of a cluster."""
    cluster = explorer.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    
    # Get all summaries for this cluster
    with Session(explorer.engine) as session:
        stmt = select(SummaryDB).join(
            ClusterConversationLink,
            SummaryDB.chat_id == ClusterConversationLink.conversation_id
        ).where(
            ClusterConversationLink.cluster_id == cluster_id
        )
        summaries = session.exec(stmt).all()
    
    # Aggregate data
    total_convs = len(summaries)
    
    # Language distribution
    language_counts = {}
    for s in summaries:
        if s.languages:
            for lang in s.languages:
                language_counts[lang] = language_counts.get(lang, 0) + 1
    
    # Frustration distribution
    frustration_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for s in summaries:
        if s.user_frustration:
            frustration_dist[s.user_frustration] += 1
    
    # Common tasks
    task_counts = {}
    for s in summaries:
        if s.task:
            task_counts[s.task] = task_counts.get(s.task, 0) + 1
    
    # Top tasks
    top_tasks = sorted(task_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "cluster_id": cluster_id,
        "cluster_name": cluster.name,
        "total_conversations": total_convs,
        "language_distribution": language_counts,
        "frustration_distribution": frustration_dist,
        "top_tasks": [{"task": t[0], "count": t[1]} for t in top_tasks],
        "sample_summaries": [s.summary for s in summaries[:5]]
    }