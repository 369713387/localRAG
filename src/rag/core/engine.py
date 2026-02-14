"""RAG main engine."""
from typing import Any

from rag.core.chunker import Chunk
from rag.core.config import settings
from rag.core.exceptions import RAGError
from rag.core.retriever import Retriever


class RAGEngine:
    """RAG main engine for question answering."""

    def __init__(
        self,
        retriever: Retriever,
        llm_client: Any,
        memory: Any,
    ):
        self.retriever = retriever
        self.llm_client = llm_client
        self.memory = memory
        self.top_k = settings.top_k

    async def query(
        self,
        question: str,
        conversation_id: str | None = None,
        top_k: int | None = None,
    ) -> dict[str, Any]:
        """
        Execute a query and get an answer.

        Args:
            question: User question
            conversation_id: Optional conversation ID for context
            top_k: Number of documents to retrieve

        Returns:
            Dictionary containing answer and sources
        """
        top_k = top_k or self.top_k

        try:
            # 1. Retrieve relevant documents
            retrieved_docs = await self.retriever.retrieve(question, top_k=top_k)

            # 2. Get conversation history
            history = []
            if conversation_id:
                history = self.memory.get_history(conversation_id)

            # 3. Build prompt
            prompt = self._build_prompt(question, retrieved_docs, history)

            # 4. Call LLM to generate answer
            answer = await self.llm_client.generate(prompt)

            # 5. Update conversation history
            if conversation_id:
                self.memory.add_exchange(
                    conversation_id, question, answer
                )

            return {
                "answer": answer,
                "sources": [
                    {
                        "doc_id": doc.metadata.get("doc_id", "unknown"),
                        "title": doc.metadata.get("title", "Untitled"),
                        "score": doc.metadata.get("score", 0.0),
                    }
                    for doc in retrieved_docs
                ],
                "conversation_id": conversation_id,
            }

        except Exception as e:
            raise RAGError(f"Query processing failed: {e}", cause=e)

    def _build_prompt(
        self,
        question: str,
        docs: list[Chunk],
        history: list[dict],
    ) -> str:
        """Build the prompt for the LLM."""
        # Build context from documents
        context = "\n\n".join(
            f"[Document {i + 1}]\n{doc.content}"
            for i, doc in enumerate(docs)
        )

        # Build history text
        history_text = ""
        if history:
            history_text = "\n".join(
                f"User: {h['question']}\nAssistant: {h['answer']}"
                for h in history
            )

        # Assemble prompt
        prompt = f"""You are a knowledge base assistant. Please answer the user's question based on the following document content.
If there is no relevant information in the documents, please honestly say "I could not find relevant information."

### Reference Documents:
{context}

### Conversation History:
{history_text if history_text else "(No conversation history)"}

### User Question:
{question}

### Answer:"""

        return prompt

    async def ingest_documents(self, documents: list[dict[str, Any]]) -> int:
        """
        Ingest documents into the knowledge base.

        Args:
            documents: List of documents, each containing content and metadata

        Returns:
            Number of successfully ingested documents
        """
        count = 0
        for doc in documents:
            try:
                await self.retriever.index_document(
                    content=doc["content"],
                    metadata=doc.get("metadata", {}),
                )
                count += 1
            except Exception as e:
                # Log error but continue processing
                print(f"Failed to ingest document: {e}")

        return count
