"""ChromaDB vector storage."""
import logging
import uuid
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from rag.core.config import settings
from rag.core.exceptions import RetrievalError

logger = logging.getLogger(__name__)


class ChromaStore:
    """ChromaDB vector storage for document embeddings."""

    def __init__(
        self,
        persist_dir: Optional[str] = None,
        collection_name: Optional[str] = None,
    ):
        """
        Initialize ChromaDB vector store.

        Args:
            persist_dir: Directory for ChromaDB persistence. Uses settings if not provided.
            collection_name: Name of the collection. Uses settings if not provided.
        """
        self.persist_dir = persist_dir or str(settings.chroma_persist_dir)
        self.collection_name = collection_name or settings.chroma_collection

        logger.info(f"Initializing ChromaStore at: {self.persist_dir}")

        # Initialize client with persistent storage
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(
                anonymized_telemetry=False,
            ),
        )

        # Get or create collection with cosine similarity space
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        logger.info(
            f"ChromaStore initialized with collection '{self.collection_name}', "
            f"containing {self.collection.count()} documents"
        )

    def add(
        self,
        content: str,
        embedding: list[float],
        metadata: dict,
        doc_id: Optional[str] = None,
    ) -> str:
        """
        Add a document to the vector store.

        Args:
            content: Document content text.
            embedding: Embedding vector for the document.
            metadata: Metadata dictionary for the document.
            doc_id: Optional document ID. Auto-generated if not provided.

        Returns:
            The document ID.

        Raises:
            RetrievalError: If adding the document fails.
        """
        doc_id = doc_id or str(uuid.uuid4())

        try:
            self.collection.add(
                ids=[doc_id],
                documents=[content],
                embeddings=[embedding],
                metadatas=[metadata],
            )

            logger.debug(f"Added document with ID: {doc_id}")
            return doc_id

        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            raise RetrievalError(f"Failed to add document: {e}", cause=e)

    def add_batch(
        self,
        contents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
        doc_ids: Optional[list[str]] = None,
    ) -> list[str]:
        """
        Add multiple documents to the vector store in batch.

        Args:
            contents: List of document content texts.
            embeddings: List of embedding vectors.
            metadatas: List of metadata dictionaries.
            doc_ids: Optional list of document IDs. Auto-generated if not provided.

        Returns:
            List of document IDs.

        Raises:
            RetrievalError: If batch add fails.
        """
        doc_ids = doc_ids or [str(uuid.uuid4()) for _ in contents]

        try:
            self.collection.add(
                ids=doc_ids,
                documents=contents,
                embeddings=embeddings,
                metadatas=metadatas,
            )

            logger.debug(f"Added {len(doc_ids)} documents in batch")
            return doc_ids

        except Exception as e:
            logger.error(f"Failed to add documents in batch: {e}")
            raise RetrievalError(f"Failed to add documents in batch: {e}", cause=e)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: Optional[dict] = None,
    ) -> list[dict]:
        """
        Search for similar documents using vector similarity.

        Args:
            query_embedding: Query embedding vector.
            top_k: Number of results to return.
            filters: Optional metadata filters to apply.

        Returns:
            List of search results, each containing:
                - id: Document ID
                - content: Document content
                - metadata: Document metadata
                - score: Similarity score (higher is more similar)

        Raises:
            RetrievalError: If search fails.
        """
        where = filters if filters else None

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where,
                include=["documents", "metadatas", "distances"],
            )

            # Format results into a more convenient structure
            formatted_results = []
            if results["ids"] and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    formatted_results.append(
                        {
                            "id": results["ids"][0][i],
                            "content": results["documents"][0][i],
                            "metadata": results["metadatas"][0][i],
                            "score": 1 - results["distances"][0][i],  # Convert distance to similarity
                        }
                    )

            logger.debug(f"Found {len(formatted_results)} results for query")
            return formatted_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise RetrievalError(f"Search failed: {e}", cause=e)

    def delete(self, doc_id: str) -> bool:
        """
        Delete a document from the vector store.

        Args:
            doc_id: Document ID to delete.

        Returns:
            True if deletion was successful, False otherwise.
        """
        try:
            self.collection.delete(ids=[doc_id])
            logger.debug(f"Deleted document with ID: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            return False

    def delete_batch(self, doc_ids: list[str]) -> bool:
        """
        Delete multiple documents from the vector store.

        Args:
            doc_ids: List of document IDs to delete.

        Returns:
            True if deletion was successful, False otherwise.
        """
        try:
            self.collection.delete(ids=doc_ids)
            logger.debug(f"Deleted {len(doc_ids)} documents in batch")
            return True
        except Exception as e:
            logger.error(f"Failed to delete documents in batch: {e}")
            return False

    def count(self) -> int:
        """
        Get the number of documents in the collection.

        Returns:
            Number of documents.
        """
        return self.collection.count()

    def get_stats(self) -> dict:
        """
        Get storage statistics.

        Returns:
            Dictionary containing:
                - collection_name: Name of the collection
                - document_count: Number of documents
                - persist_directory: Path to persistence directory
        """
        return {
            "collection_name": self.collection_name,
            "document_count": self.count(),
            "persist_directory": self.persist_dir,
        }
