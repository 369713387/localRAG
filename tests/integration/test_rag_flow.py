"""RAG flow integration tests."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from rag.core.engine import RAGEngine
from rag.core.retriever import Retriever
from rag.core.chunker import Chunk


class TestRAGFlow:
    """RAG flow integration tests using mocks."""

    @pytest.fixture
    def mock_retriever(self) -> MagicMock:
        """Create a mock retriever."""
        retriever = MagicMock(spec=Retriever)
        retriever.retrieve = AsyncMock(
            return_value=[
                Chunk(
                    content="Test document content for retrieval",
                    metadata={"doc_id": "doc-1", "title": "Test Document", "score": 0.95},
                    chunk_id=0,
                    source="test_source",
                ),
                Chunk(
                    content="Another test document",
                    metadata={"doc_id": "doc-2", "title": "Second Document", "score": 0.85},
                    chunk_id=1,
                    source="test_source_2",
                ),
            ]
        )
        retriever.index_document = AsyncMock(return_value="doc-new-id")
        return retriever

    @pytest.fixture
    def mock_llm(self) -> MagicMock:
        """Create a mock LLM client."""
        llm = MagicMock()
        llm.generate = AsyncMock(return_value="This is a test answer from the LLM.")
        return llm

    @pytest.fixture
    def mock_memory(self) -> MagicMock:
        """Create a mock conversation memory."""
        memory = MagicMock()
        memory.get_history = MagicMock(return_value=[])
        memory.add_exchange = MagicMock()
        memory.create_conversation = MagicMock(return_value="conv-1")
        return memory

    @pytest.mark.asyncio
    async def test_query_flow(
        self,
        mock_retriever: MagicMock,
        mock_llm: MagicMock,
        mock_memory: MagicMock,
    ) -> None:
        """Test the complete query flow."""
        engine = RAGEngine(
            retriever=mock_retriever,
            llm_client=mock_llm,
            memory=mock_memory,
        )

        result = await engine.query("What is the test question?", conversation_id="conv-1")

        # Verify the result structure
        assert "answer" in result
        assert "sources" in result
        assert "conversation_id" in result

        # Verify the answer
        assert result["answer"] == "This is a test answer from the LLM."

        # Verify sources were returned
        assert len(result["sources"]) == 2
        assert result["sources"][0]["doc_id"] == "doc-1"
        assert result["sources"][0]["title"] == "Test Document"
        assert result["sources"][0]["score"] == 0.95

        # Verify method calls
        mock_retriever.retrieve.assert_called_once()
        mock_llm.generate.assert_called_once()
        mock_memory.get_history.assert_called_once_with("conv-1")
        mock_memory.add_exchange.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_flow_without_conversation(
        self,
        mock_retriever: MagicMock,
        mock_llm: MagicMock,
        mock_memory: MagicMock,
    ) -> None:
        """Test query flow without conversation ID."""
        engine = RAGEngine(
            retriever=mock_retriever,
            llm_client=mock_llm,
            memory=mock_memory,
        )

        result = await engine.query("Test question without conversation")

        # Verify the result
        assert "answer" in result
        assert result["conversation_id"] is None

        # Memory should not be accessed without conversation_id
        mock_memory.get_history.assert_not_called()
        mock_memory.add_exchange.assert_not_called()

    @pytest.mark.asyncio
    async def test_query_flow_with_history(
        self,
        mock_retriever: MagicMock,
        mock_llm: MagicMock,
    ) -> None:
        """Test query flow with conversation history."""
        mock_memory = MagicMock()
        mock_memory.get_history = MagicMock(
            return_value=[
                {"question": "Previous question", "answer": "Previous answer"}
            ]
        )
        mock_memory.add_exchange = MagicMock()

        engine = RAGEngine(
            retriever=mock_retriever,
            llm_client=mock_llm,
            memory=mock_memory,
        )

        result = await engine.query("Follow-up question", conversation_id="conv-1")

        assert "answer" in result
        mock_memory.get_history.assert_called_once_with("conv-1")

    @pytest.mark.asyncio
    async def test_ingest_documents(
        self,
        mock_retriever: MagicMock,
        mock_llm: MagicMock,
        mock_memory: MagicMock,
    ) -> None:
        """Test document ingestion flow."""
        engine = RAGEngine(
            retriever=mock_retriever,
            llm_client=mock_llm,
            memory=mock_memory,
        )

        documents = [
            {"content": "First document content", "metadata": {"title": "Doc 1"}},
            {"content": "Second document content", "metadata": {"title": "Doc 2"}},
            {"content": "Third document content", "metadata": {"title": "Doc 3"}},
        ]

        count = await engine.ingest_documents(documents)

        assert count == 3
        assert mock_retriever.index_document.call_count == 3

    @pytest.mark.asyncio
    async def test_ingest_documents_partial_failure(
        self,
        mock_llm: MagicMock,
        mock_memory: MagicMock,
    ) -> None:
        """Test document ingestion with partial failures."""
        mock_retriever = MagicMock(spec=Retriever)
        # First call succeeds, second fails, third succeeds
        mock_retriever.index_document = AsyncMock(
            side_effect=[
                "doc-1",
                Exception("Indexing failed"),
                "doc-3",
            ]
        )

        engine = RAGEngine(
            retriever=mock_retriever,
            llm_client=mock_llm,
            memory=mock_memory,
        )

        documents = [
            {"content": "First document", "metadata": {}},
            {"content": "Second document", "metadata": {}},
            {"content": "Third document", "metadata": {}},
        ]

        count = await engine.ingest_documents(documents)

        # Only 2 documents should be counted as successful
        assert count == 2

    @pytest.mark.asyncio
    async def test_query_flow_custom_top_k(
        self,
        mock_retriever: MagicMock,
        mock_llm: MagicMock,
        mock_memory: MagicMock,
    ) -> None:
        """Test query flow with custom top_k parameter."""
        engine = RAGEngine(
            retriever=mock_retriever,
            llm_client=mock_llm,
            memory=mock_memory,
        )

        await engine.query("Test question", top_k=10)

        # Verify retrieve was called with custom top_k
        call_args = mock_retriever.retrieve.call_args
        assert call_args[1]["top_k"] == 10

    @pytest.mark.asyncio
    async def test_query_flow_empty_results(
        self,
        mock_llm: MagicMock,
        mock_memory: MagicMock,
    ) -> None:
        """Test query flow when no documents are retrieved."""
        mock_retriever = MagicMock(spec=Retriever)
        mock_retriever.retrieve = AsyncMock(return_value=[])

        engine = RAGEngine(
            retriever=mock_retriever,
            llm_client=mock_llm,
            memory=mock_memory,
        )

        result = await engine.query("Test question with no results")

        assert "answer" in result
        assert "sources" in result
        assert len(result["sources"]) == 0
        mock_llm.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_prompt_building_includes_context(
        self,
        mock_retriever: MagicMock,
        mock_llm: MagicMock,
        mock_memory: MagicMock,
    ) -> None:
        """Test that the prompt includes document context."""
        engine = RAGEngine(
            retriever=mock_retriever,
            llm_client=mock_llm,
            memory=mock_memory,
        )

        await engine.query("What is the context?")

        # Get the prompt that was passed to LLM
        call_args = mock_llm.generate.call_args
        prompt = call_args[0][0]

        # Verify prompt contains key elements
        assert "What is the context?" in prompt
        assert "Test document content" in prompt
        assert "Reference Documents" in prompt or "Document" in prompt
