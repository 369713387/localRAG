"""Document chunker implementation."""
from dataclasses import dataclass
from typing import Generator


@dataclass
class Chunk:
    """Document chunk."""

    content: str
    metadata: dict
    chunk_id: int
    source: str


class TextChunker:
    """Text chunker for splitting documents into smaller pieces."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(
        self, text: str, source: str, metadata: dict | None = None
    ) -> list[Chunk]:
        """
        Split text into chunks.

        Args:
            text: Text to split
            source: Source identifier
            metadata: Additional metadata

        Returns:
            List of document chunks
        """
        if metadata is None:
            metadata = {}

        if not text.strip():
            return []

        chunks = []
        start = 0
        chunk_id = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]

            # Try to split at sentence boundary
            if end < len(text):
                last_period = chunk_text.rfind("。")
                last_newline = chunk_text.rfind("\n")
                break_point = max(last_period, last_newline)

                if break_point > self.chunk_size // 2:
                    end = start + break_point + 1
                    chunk_text = text[start:end]

            chunk = Chunk(
                content=chunk_text.strip(),
                metadata={**metadata, "source": source},
                chunk_id=chunk_id,
                source=source,
            )
            chunks.append(chunk)

            chunk_id += 1
            next_start = end - self.chunk_overlap

            # Prevent infinite loop when overlap causes start to not advance
            if next_start <= start:
                break

            start = next_start

        return chunks

    def chunk_generator(
        self, text: str, source: str, metadata: dict | None = None
    ) -> Generator[Chunk, None, None]:
        """Generator version of the chunk method."""
        yield from self.chunk(text, source, metadata)
