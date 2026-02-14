"""Chat/QA routes for RAG system."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter()

# Global engine instance (initialized lazily)
_engine = None
_memory = None


def get_engine_and_memory():
    """Get or create the RAG engine and memory instances."""
    global _engine, _memory

    if _engine is None or _memory is None:
        from rag.core.engine import RAGEngine
        from rag.core.retriever import Retriever
        from rag.embeddings.glm_embedding import GLMEmbedding
        from rag.llm.glm_client import GLMClient
        from rag.memory.conversation import ConversationMemory
        from rag.storage.chroma_store import ChromaStore

        embedding = GLMEmbedding()
        store = ChromaStore()
        retriever = Retriever(embedding, store)
        llm = GLMClient()
        _memory = ConversationMemory()
        _engine = RAGEngine(retriever, llm, _memory)

    return _engine, _memory


class ChatRequest(BaseModel):
    """Request model for chat/QA endpoint."""

    query: str = Field(..., description="The user's question", min_length=1)
    conversation_id: Optional[str] = Field(
        None, description="Optional conversation ID for context continuity"
    )
    top_k: int = Field(default=5, description="Number of documents to retrieve", ge=1, le=20)


class Source(BaseModel):
    """Model for a source document in the response."""

    doc_id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    score: float = Field(..., description="Relevance score")


class ChatResponse(BaseModel):
    """Response model for chat/QA endpoint."""

    answer: str = Field(..., description="The generated answer")
    sources: list[Source] = Field(default_factory=list, description="Source documents used")
    conversation_id: str = Field(..., description="Conversation ID for future context")


class HistoryItem(BaseModel):
    """Model for a single history item."""

    question: str = Field(..., description="User's question")
    answer: str = Field(..., description="Assistant's answer")


class HistoryResponse(BaseModel):
    """Response model for conversation history."""

    conversation_id: str = Field(..., description="Conversation ID")
    history: list[HistoryItem] = Field(
        default_factory=list, description="List of Q&A pairs"
    )


class ClearHistoryResponse(BaseModel):
    """Response model for clearing history."""

    status: str = Field(..., description="Operation status")
    conversation_id: str = Field(..., description="Conversation ID that was cleared")


@router.post("", response_model=ChatResponse, summary="Ask a question")
async def chat(request: ChatRequest) -> ChatResponse:
    """Ask a question to the RAG system.

    This endpoint processes a user question, retrieves relevant documents,
    and generates an answer using the LLM.

    Args:
        request: ChatRequest containing the query and optional parameters

    Returns:
        ChatResponse with the answer, sources, and conversation ID

    Raises:
        HTTPException: If the query processing fails
    """
    engine, memory = get_engine_and_memory()

    # Create or use existing conversation
    conversation_id = request.conversation_id
    if not conversation_id:
        conversation_id = memory.create_conversation()

    try:
        # Execute query
        result = await engine.query(
            question=request.query,
            conversation_id=conversation_id,
            top_k=request.top_k,
        )

        return ChatResponse(
            answer=result["answer"],
            sources=[
                Source(
                    doc_id=s["doc_id"],
                    title=s["title"],
                    score=s["score"],
                )
                for s in result["sources"]
            ],
            conversation_id=conversation_id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}",
        )


@router.get(
    "/history",
    response_model=HistoryResponse,
    summary="Get conversation history",
)
async def get_history(
    conversation_id: str = Query(..., description="Conversation ID to get history for"),
) -> HistoryResponse:
    """Get the conversation history for a specific conversation.

    Args:
        conversation_id: The ID of the conversation

    Returns:
        HistoryResponse containing the conversation ID and history items
    """
    _, memory = get_engine_and_memory()

    history = memory.get_history(conversation_id)

    return HistoryResponse(
        conversation_id=conversation_id,
        history=[
            HistoryItem(question=h["question"], answer=h["answer"])
            for h in history
        ],
    )


@router.delete(
    "/history",
    response_model=ClearHistoryResponse,
    summary="Clear conversation history",
)
async def clear_history(
    conversation_id: str = Query(..., description="Conversation ID to clear"),
) -> ClearHistoryResponse:
    """Clear the conversation history for a specific conversation.

    Args:
        conversation_id: The ID of the conversation to clear

    Returns:
        ClearHistoryResponse confirming the operation
    """
    _, memory = get_engine_and_memory()

    memory.clear_history(conversation_id)

    return ClearHistoryResponse(
        status="cleared",
        conversation_id=conversation_id,
    )
