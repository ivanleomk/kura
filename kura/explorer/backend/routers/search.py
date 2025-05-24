"""Search API router."""

from fastapi import APIRouter, HTTPException, Query, Depends

from kura.explorer.backend.models import (
    SearchResult,
    ConversationResponse,
    SummaryResponse,
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


@router.get("", response_model=SearchResult)
async def search_conversations(
    q: str = Query(..., description="Search query", min_length=2),
    limit: int = Query(50, ge=1, le=200),
    explorer: KuraExplorer = Depends(get_explorer),
):
    """Search across all conversations and summaries."""
    results = explorer.search_conversations(q)[:limit]

    conversations = []
    for conv in results:
        summary = explorer.get_summary(conv.chat_id)

        conversations.append(
            ConversationResponse(
                id=conv.chat_id,
                created_at=conv.created_at,
                metadata=conv.metadata_json,
                message_count=conv.message_count,
                summary=SummaryResponse(**summary.__dict__) if summary else None,
                cluster_names=[c.name for c in conv.clusters[:3]],
            )
        )

    return SearchResult(conversations=conversations, total_count=len(results), query=q)
