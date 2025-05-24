"""Conversations API router."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends

from models import (
    ConversationResponse, ConversationDetailResponse,
    PaginatedResponse, SummaryResponse, MessageResponse
)
from kura.explorer.api import KuraExplorer


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
async def get_conversations(
    cluster_id: Optional[str] = Query(None, description="Filter by cluster ID"),
    search: Optional[str] = Query(None, description="Search in summaries"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    language: Optional[str] = Query(None, description="Filter by language"),
    min_frustration: Optional[int] = Query(None, ge=1, le=5),
    max_frustration: Optional[int] = Query(None, ge=1, le=5),
    explorer: KuraExplorer = Depends(get_explorer)
):
    """Get conversations with pagination and filtering."""
    from sqlmodel import Session, select, func
    from kura.explorer.db.models import ConversationDB, SummaryDB, ClusterConversationLink, ClusterDB
    from sqlalchemy.orm import selectinload
    
    with Session(explorer.engine) as session:
        # Build base query
        query = select(ConversationDB).options(
            selectinload(ConversationDB.summary),
            selectinload(ConversationDB.clusters)
        )
        
        # Count query for total
        count_query = select(func.count()).select_from(ConversationDB)
        
        # Apply filters
        if cluster_id:
            query = query.join(ClusterConversationLink).where(
                ClusterConversationLink.cluster_id == cluster_id
            )
            count_query = count_query.join(ClusterConversationLink).where(
                ClusterConversationLink.cluster_id == cluster_id
            )
        
        if search:
            query = query.join(SummaryDB).where(
                SummaryDB.summary.contains(search) |
                SummaryDB.task.contains(search) |
                SummaryDB.request.contains(search)
            )
            count_query = count_query.join(SummaryDB).where(
                SummaryDB.summary.contains(search) |
                SummaryDB.task.contains(search) |
                SummaryDB.request.contains(search)
            )
        
        if language or min_frustration or max_frustration:
            query = query.join(SummaryDB, isouter=True)
            count_query = count_query.join(SummaryDB, isouter=True)
            
            if language:
                # SQLite JSON operations
                query = query.where(
                    SummaryDB.languages.contains(f'"{language}"')
                )
                count_query = count_query.where(
                    SummaryDB.languages.contains(f'"{language}"')
                )
            
            if min_frustration:
                query = query.where(SummaryDB.user_frustration >= min_frustration)
                count_query = count_query.where(SummaryDB.user_frustration >= min_frustration)
            
            if max_frustration:
                query = query.where(SummaryDB.user_frustration <= max_frustration)
                count_query = count_query.where(SummaryDB.user_frustration <= max_frustration)
        
        # Get total count
        total = session.exec(count_query).one()
        
        # Get paginated results
        conversations = session.exec(
            query.order_by(ConversationDB.created_at.desc())
            .offset(offset)
            .limit(limit)
        ).all()
        
        # Convert to response models
        items = []
        for conv in conversations:
            items.append(ConversationResponse(
                id=conv.chat_id,
                created_at=conv.created_at,
                metadata=conv.metadata_json,
                message_count=conv.message_count,
                summary=SummaryResponse(**conv.summary.__dict__) if conv.summary else None,
                cluster_names=[c.name for c in conv.clusters[:3]]
            ))
        
        return PaginatedResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total
        )


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str,
    explorer: KuraExplorer = Depends(get_explorer)
):
    """Get detailed conversation with messages."""
    conv_detail = explorer.get_conversation(conversation_id)
    if not conv_detail:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return ConversationDetailResponse(
        id=conv_detail.id,
        created_at=conv_detail.created_at,
        metadata=conv_detail.metadata,
        messages=[
            MessageResponse(
                id=msg.id,
                conversation_id=msg.conversation_id,
                created_at=msg.created_at,
                role=msg.role,
                content=msg.content
            ) for msg in conv_detail.messages
        ],
        summary=SummaryResponse(**conv_detail.summary.__dict__) if conv_detail.summary else None,
        clusters=[c.name for c in conv_detail.clusters]
    )