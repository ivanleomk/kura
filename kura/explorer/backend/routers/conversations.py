"""Conversations API router."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends

from kura.explorer.backend.models import (
    ConversationResponse, ConversationDetailResponse,
    PaginatedResponse, SummaryResponse, MessageResponse
)
from kura.explorer.api import KuraExplorer


router = APIRouter()


def get_explorer() -> KuraExplorer:
    """Dependency to get explorer instance."""
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
    # Get base conversations
    conversations = explorer.get_conversations(
        limit=limit,
        offset=offset,
        cluster_id=cluster_id,
        search=search
    )
    
    # Apply additional filters
    filtered_conversations = []
    for conv in conversations:
        summary = explorer.get_summary(conv.chat_id)
        
        # Language filter
        if language and summary and summary.languages:
            if language not in summary.languages:
                continue
        
        # Frustration filters
        if summary and summary.user_frustration:
            if min_frustration and summary.user_frustration < min_frustration:
                continue
            if max_frustration and summary.user_frustration > max_frustration:
                continue
        
        filtered_conversations.append((conv, summary))
    
    # Convert to response models
    items = []
    for conv, summary in filtered_conversations:
        items.append(ConversationResponse(
            id=conv.chat_id,
            created_at=conv.created_at,
            metadata=conv.metadata_json,
            message_count=conv.message_count,
            summary=SummaryResponse(**summary.__dict__) if summary else None,
            cluster_names=[c.name for c in conv.clusters[:3]]
        ))
    
    # Get total count
    total = len(filtered_conversations)
    
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