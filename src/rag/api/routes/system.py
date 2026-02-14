"""System routes for health check and statistics."""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str


class StatsResponse(BaseModel):
    """Response model for system statistics."""

    document_count: int
    collection_name: str


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check() -> HealthResponse:
    """Check if the API is healthy and running.

    Returns:
        HealthResponse with status "healthy"
    """
    return HealthResponse(status="healthy")


@router.get("/stats", response_model=StatsResponse, summary="Get system statistics")
async def get_stats() -> StatsResponse:
    """Get system statistics including document count.

    Returns:
        StatsResponse containing document count and collection name
    """
    from rag.storage.chroma_store import ChromaStore

    store = ChromaStore()

    return StatsResponse(
        document_count=store.count(),
        collection_name=store.collection_name,
    )
