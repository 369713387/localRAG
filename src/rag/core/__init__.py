"""Core module for RAG system."""
from rag.core.config import Settings, settings
from rag.core.exceptions import (
    RAGError,
    DocumentLoadError,
    EmbeddingError,
    RetrievalError,
    LLMError,
    ConfigurationError,
)
from rag.core.chunker import Chunk, TextChunker
from rag.core.retriever import Retriever
from rag.core.engine import RAGEngine

__all__ = [
    # Config
    "Settings",
    "settings",
    # Exceptions
    "RAGError",
    "DocumentLoadError",
    "EmbeddingError",
    "RetrievalError",
    "LLMError",
    "ConfigurationError",
    # Chunker
    "Chunk",
    "TextChunker",
    # Retriever
    "Retriever",
    # Engine
    "RAGEngine",
]
