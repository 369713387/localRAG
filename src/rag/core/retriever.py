"""Retriever implementation."""
from typing import Any

from rag.core.chunker import Chunk
from rag.core.exceptions import RetrievalError


class Retriever:
    """Document retriever for vector search."""

    def __init__(
        self,
        embedding_client: Any,
        vector_store: Any,
    ):
        self.embedding_client = embedding_client
        self.vector_store = vector_store

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: dict | None = None,
    ) -> list[Chunk]:
        """
        Retrieve relevant documents.

        Args:
            query: Query text
            top_k: Number of documents to return
            filters: Metadata filter conditions

        Returns:
            List of relevant document chunks
        """
        try:
            # 1. Generate query embedding
            query_embedding = await self.embedding_client.embed(query)

            # 2. Vector search
            results = self.vector_store.search(
                query_embedding, top_k=top_k, filters=filters
            )

            # 3. Convert to Chunk objects
            chunks = []
            for result in results:
                chunk = Chunk(
                    content=result["content"],
                    metadata=result["metadata"],
                    chunk_id=result.get("id", 0),
                    source=result["metadata"].get("source", "unknown"),
                )
                chunk.metadata["score"] = result.get("score", 0.0)
                chunks.append(chunk)

            return chunks

        except Exception as e:
            raise RetrievalError(f"Retrieval failed: {e}", cause=e)

    async def index_document(
        self,
        content: str,
        metadata: dict | None = None,
        doc_id: str | None = None,
    ) -> str:
        """
        Index a single document.

        Args:
            content: Document content
            metadata: Document metadata
            doc_id: Optional document ID

        Returns:
            Document ID
        """
        try:
            # Generate embedding
            embedding = await self.embedding_client.embed(content)

            # Store in vector database
            return self.vector_store.add(
                content=content,
                embedding=embedding,
                metadata=metadata or {},
                doc_id=doc_id,
            )

        except Exception as e:
            raise RetrievalError(f"Document indexing failed: {e}", cause=e)

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document by ID."""
        try:
            return self.vector_store.delete(doc_id)
        except Exception as e:
            raise RetrievalError(f"Document deletion failed: {e}", cause=e)
