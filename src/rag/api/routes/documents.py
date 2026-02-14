"""Document management routes."""
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile

from pydantic import BaseModel

router = APIRouter()


class DocumentResponse(BaseModel):
    """Response model for a single document."""

    id: str
    filename: str
    status: str


class DocumentListResponse(BaseModel):
    """Response model for document list."""

    documents: list[DocumentResponse]
    total: int


class DeleteResponse(BaseModel):
    """Response model for document deletion."""

    status: str
    doc_id: str


@router.post("", response_model=DocumentResponse, summary="Upload a document")
async def upload_document(file: UploadFile = File(...)) -> DocumentResponse:
    """Upload and index a document to the knowledge base.

    Args:
        file: The uploaded file (supports PDF, MD, TXT, DOCX formats)

    Returns:
        DocumentResponse containing the document ID, filename, and status

    Raises:
        HTTPException: If file upload or indexing fails
    """
    from rag.core.engine import RAGEngine
    from rag.core.retriever import Retriever
    from rag.embeddings.glm_embedding import GLMEmbedding
    from rag.loaders.file_loader import FileLoader
    from rag.llm.glm_client import GLMClient
    from rag.memory.conversation import ConversationMemory
    from rag.storage.chroma_store import ChromaStore
    import tempfile
    import uuid

    # Validate file type
    allowed_extensions = {".pdf", ".md", ".txt", ".docx"}
    filename = file.filename or "unknown"

    if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}",
        )

    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=filename) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        # Load document using FileLoader
        loader = FileLoader()
        documents = loader.load(tmp_path)

        if not documents:
            raise HTTPException(status_code=400, detail="Failed to load document content")

        # Initialize RAG components
        embedding = GLMEmbedding()
        store = ChromaStore()
        retriever = Retriever(embedding, store)
        llm = GLMClient()
        memory = ConversationMemory()
        engine = RAGEngine(retriever, llm, memory)

        # Index documents
        doc_id = str(uuid.uuid4())
        docs_data = [
            {
                "content": doc.content,
                "metadata": {**doc.metadata, "doc_id": doc_id, "title": filename},
            }
            for doc in documents
        ]

        count = await engine.ingest_documents(docs_data)

        return DocumentResponse(
            id=doc_id,
            filename=filename,
            status="indexed" if count > 0 else "failed",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")


@router.get("", response_model=DocumentListResponse, summary="List documents")
async def list_documents(
    skip: int = 0,
    limit: int = 20,
) -> DocumentListResponse:
    """List all indexed documents with pagination.

    Args:
        skip: Number of documents to skip (for pagination)
        limit: Maximum number of documents to return

    Returns:
        DocumentListResponse containing list of documents and total count
    """
    from rag.storage.chroma_store import ChromaStore

    store = ChromaStore()

    # Get all documents from the collection
    # Note: ChromaDB doesn't support native pagination, so we get all and slice
    all_docs = store.collection.get(
        include=["metadatas"],
    )

    documents = []
    seen_ids = set()

    if all_docs and all_docs.get("ids"):
        # Deduplicate by doc_id
        for i, doc_id in enumerate(all_docs["ids"]):
            metadata = all_docs["metadatas"][i] if all_docs.get("metadatas") else {}
            unique_id = metadata.get("doc_id", doc_id)

            if unique_id not in seen_ids:
                seen_ids.add(unique_id)
                documents.append(
                    DocumentResponse(
                        id=unique_id,
                        filename=metadata.get("filename", metadata.get("title", "Unknown")),
                        status="indexed",
                    )
                )

    # Apply pagination
    total = len(documents)
    paginated_docs = documents[skip : skip + limit]

    return DocumentListResponse(
        documents=paginated_docs,
        total=total,
    )


@router.delete("/{doc_id}", response_model=DeleteResponse, summary="Delete a document")
async def delete_document(doc_id: str) -> DeleteResponse:
    """Delete a document from the knowledge base.

    Args:
        doc_id: The ID of the document to delete

    Returns:
        DeleteResponse confirming the deletion

    Raises:
        HTTPException: If document deletion fails
    """
    from rag.storage.chroma_store import ChromaStore

    store = ChromaStore()

    # Find all chunks with this doc_id
    all_docs = store.collection.get(
        where={"doc_id": doc_id},
        include=["metadatas"],
    )

    if not all_docs or not all_docs.get("ids"):
        raise HTTPException(status_code=404, detail=f"Document not found: {doc_id}")

    # Delete all chunks associated with this document
    success = store.delete_batch(all_docs["ids"])

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete document")

    return DeleteResponse(
        status="deleted",
        doc_id=doc_id,
    )
