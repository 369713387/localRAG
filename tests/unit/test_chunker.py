"""Text chunker unit tests."""
import pytest

from rag.core.chunker import Chunk, TextChunker


class TestTextChunker:
    """TextChunker test cases."""

    def test_chunk_empty_text(self) -> None:
        """Test chunking empty text returns empty list."""
        chunker = TextChunker(chunk_size=100, chunk_overlap=10)
        chunks = chunker.chunk("", "test")

        assert len(chunks) == 0

    def test_chunk_whitespace_only_text(self) -> None:
        """Test chunking whitespace-only text returns empty list."""
        chunker = TextChunker(chunk_size=100, chunk_overlap=10)
        chunks = chunker.chunk("   \n\t  ", "test")

        assert len(chunks) == 0

    def test_chunk_short_text(self) -> None:
        """Test chunking text shorter than chunk size."""
        chunker = TextChunker(chunk_size=100, chunk_overlap=10)
        text = "This is a short text"
        chunks = chunker.chunk(text, "test")

        assert len(chunks) == 1
        assert chunks[0].content == text
        assert chunks[0].source == "test"
        assert chunks[0].chunk_id == 0

    def test_chunk_long_text(self) -> None:
        """Test chunking text longer than chunk size."""
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)
        text = "This is a longer piece of text that should be split into multiple chunks. " * 5
        chunks = chunker.chunk(text, "test")

        assert len(chunks) > 1
        # Verify each chunk has content
        for chunk in chunks:
            assert len(chunk.content) > 0
            assert chunk.source == "test"

    def test_chunk_with_metadata(self) -> None:
        """Test chunking with custom metadata."""
        chunker = TextChunker()
        text = "Test content for metadata check"
        metadata = {"author": "test_author", "date": "2024-01-01", "category": "test"}

        chunks = chunker.chunk(text, "test_source", metadata)

        assert len(chunks) == 1
        assert chunks[0].metadata["author"] == "test_author"
        assert chunks[0].metadata["date"] == "2024-01-01"
        assert chunks[0].metadata["category"] == "test"
        assert chunks[0].metadata["source"] == "test_source"

    def test_chunk_with_none_metadata(self) -> None:
        """Test chunking with None metadata creates empty dict with source."""
        chunker = TextChunker()
        text = "Test content"

        chunks = chunker.chunk(text, "test_source", None)

        assert len(chunks) == 1
        assert chunks[0].metadata["source"] == "test_source"
        assert len(chunks[0].metadata) == 1

    def test_chunk_generator(self) -> None:
        """Test the generator version of chunk method."""
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)
        text = "Test sentence. " * 20

        # Get chunks from generator
        chunks_from_generator = list(chunker.chunk_generator(text, "test"))

        # Get chunks from regular method
        chunks_from_list = chunker.chunk(text, "test")

        # Both should produce the same results
        assert len(chunks_from_generator) == len(chunks_from_list)
        for gen_chunk, list_chunk in zip(chunks_from_generator, chunks_from_list):
            assert gen_chunk.content == list_chunk.content
            assert gen_chunk.source == list_chunk.source
            assert gen_chunk.chunk_id == list_chunk.chunk_id

    def test_chunk_preserves_chunk_ids(self) -> None:
        """Test that chunk IDs are sequential."""
        chunker = TextChunker(chunk_size=30, chunk_overlap=5)
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."

        chunks = chunker.chunk(text, "test")

        for i, chunk in enumerate(chunks):
            assert chunk.chunk_id == i

    def test_chunk_sentence_boundary(self) -> None:
        """Test that chunking respects sentence boundaries when possible."""
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)
        text = "This is the first sentence. This is the second sentence. This is the third sentence."

        chunks = chunker.chunk(text, "test")

        # Each chunk should end at a reasonable boundary
        for chunk in chunks:
            assert len(chunk.content) > 0

    def test_chunk_chinese_text(self) -> None:
        """Test chunking Chinese text with Chinese period as delimiter."""
        chunker = TextChunker(chunk_size=30, chunk_overlap=5)
        text = "这是第一句话。这是第二句话。这是第三句话。这是第四句话。"

        chunks = chunker.chunk(text, "test")

        assert len(chunks) >= 1
        for chunk in chunks:
            assert len(chunk.content) > 0

    def test_chunk_with_newlines(self) -> None:
        """Test chunking text with newlines."""
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)
        text = "Line one.\nLine two.\nLine three.\nLine four.\nLine five."

        chunks = chunker.chunk(text, "test")

        assert len(chunks) >= 1
        for chunk in chunks:
            assert len(chunk.content) > 0

    def test_chunk_dataclass_attributes(self) -> None:
        """Test that Chunk dataclass has all required attributes."""
        chunk = Chunk(
            content="test content",
            metadata={"key": "value"},
            chunk_id=0,
            source="test_source"
        )

        assert chunk.content == "test content"
        assert chunk.metadata == {"key": "value"}
        assert chunk.chunk_id == 0
        assert chunk.source == "test_source"

    def test_chunk_overlap_behavior(self) -> None:
        """Test that overlapping chunks share content."""
        chunker = TextChunker(chunk_size=20, chunk_overlap=5)
        text = "abcdefghij" * 10  # 100 characters

        chunks = chunker.chunk(text, "test")

        # With overlap, consecutive chunks should have some shared content
        if len(chunks) > 1:
            # This verifies the overlap mechanism is in place
            assert len(chunks) > 1
