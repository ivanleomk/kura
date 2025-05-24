"""Conversations API router."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends

from models import (
    ConversationResponse,
    ConversationDetailResponse,
    PaginatedConversationResponse,
    SummaryResponse,
    MessageResponse,
    ConversationFacets,
    FrustrationFacets,
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


@router.get("", response_model=PaginatedConversationResponse)
async def get_conversations(
    cluster_id: Optional[str] = Query(None, description="Filter by cluster ID"),
    search: Optional[str] = Query(None, description="Search in summaries"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    language: Optional[str] = Query(None, description="Filter by language"),
    min_frustration: Optional[int] = Query(None, ge=1, le=5),
    max_frustration: Optional[int] = Query(None, ge=1, le=5),
    explorer: KuraExplorer = Depends(get_explorer),
):
    """Get conversations with pagination and filtering, including facet counts."""
    from sqlmodel import Session, select, func, case
    from kura.explorer.db.models import (
        ConversationDB,
        SummaryDB,
        ClusterConversationLink,
    )
    from sqlalchemy.orm import selectinload

    with Session(explorer.engine) as session:
        # Build base query
        query = select(ConversationDB).options(
            selectinload(ConversationDB.summary), selectinload(ConversationDB.clusters)
        )

        # Count query for total
        count_query = select(func.count()).select_from(ConversationDB)

        # Base query for facets (before pagination)
        facet_base_query = select(ConversationDB).join(SummaryDB, isouter=True)

        # Apply filters to all queries
        if cluster_id:
            cluster_filter = ClusterConversationLink.cluster_id == cluster_id
            query = query.join(ClusterConversationLink).where(cluster_filter)
            count_query = count_query.join(ClusterConversationLink).where(
                cluster_filter
            )
            facet_base_query = facet_base_query.join(ClusterConversationLink).where(
                cluster_filter
            )

        if search:
            search_filter = (
                SummaryDB.summary.contains(search)
                | SummaryDB.task.contains(search)
                | SummaryDB.request.contains(search)
            )
            query = query.join(SummaryDB).where(search_filter)
            count_query = count_query.join(SummaryDB).where(search_filter)
            facet_base_query = facet_base_query.where(search_filter)

        if language or min_frustration or max_frustration:
            query = query.join(SummaryDB, isouter=True)
            count_query = count_query.join(SummaryDB, isouter=True)

            if language:
                # SQLite JSON operations
                language_filter = SummaryDB.languages.contains(f'"{language}"')
                query = query.where(language_filter)
                count_query = count_query.where(language_filter)
                facet_base_query = facet_base_query.where(language_filter)

            if min_frustration:
                min_filter = SummaryDB.user_frustration >= min_frustration
                query = query.where(min_filter)
                count_query = count_query.where(min_filter)
                facet_base_query = facet_base_query.where(min_filter)

            if max_frustration:
                max_filter = SummaryDB.user_frustration <= max_frustration
                query = query.where(max_filter)
                count_query = count_query.where(max_filter)
                facet_base_query = facet_base_query.where(max_filter)

        # Calculate facets (frustration level counts)
        frustration_facet_query = select(
            func.sum(
                case((SummaryDB.user_frustration.between(1, 2), 1), else_=0)
            ).label("low"),
            func.sum(case((SummaryDB.user_frustration == 3, 1), else_=0)).label(
                "medium"
            ),
            func.sum(case((SummaryDB.user_frustration == 4, 1), else_=0)).label("high"),
            func.sum(case((SummaryDB.user_frustration >= 5, 1), else_=0)).label(
                "critical"
            ),
        ).select_from(facet_base_query.subquery())

        facet_result = session.exec(frustration_facet_query).first()

        frustration_facets = FrustrationFacets(
            low=facet_result.low or 0,
            medium=facet_result.medium or 0,
            high=facet_result.high or 0,
            critical=facet_result.critical or 0,
        )

        # Get total count
        total = session.exec(count_query).one()

        # Get paginated results
        conversations = session.exec(
            query.order_by(ConversationDB.created_at.desc()).offset(offset).limit(limit)
        ).all()

        # Convert to response models
        items = []
        for conv in conversations:
            items.append(
                ConversationResponse(
                    id=conv.chat_id,
                    created_at=conv.created_at,
                    metadata=conv.metadata_json,
                    message_count=conv.message_count,
                    summary=SummaryResponse(**conv.summary.__dict__)
                    if conv.summary
                    else None,
                    cluster_names=[c.name for c in conv.clusters[:3]],
                )
            )

        return PaginatedConversationResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
            facets=ConversationFacets(frustration_levels=frustration_facets),
        )


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str, explorer: KuraExplorer = Depends(get_explorer)
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
                content=msg.content,
            )
            for msg in conv_detail.messages
        ],
        summary=SummaryResponse(**conv_detail.summary.__dict__)
        if conv_detail.summary
        else None,
        clusters=[c.name for c in conv_detail.clusters],
    )
