"""GLM Embedding client."""
import logging
from typing import Optional

from tenacity import retry, stop_after_attempt, wait_exponential
from zhipuai import ZhipuAI

from rag.core.config import settings
from rag.core.exceptions import EmbeddingError

logger = logging.getLogger(__name__)


class GLMEmbedding:
    """GLM Embedding client for generating text embeddings using Zhipu AI."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize the GLM Embedding client.

        Args:
            api_key: Zhipu AI API key. If not provided, uses settings.
            model: Embedding model name. If not provided, uses settings.
        """
        self.api_key = api_key or settings.get_embedding_api_key()
        self.model = model or settings.zhipu_embedding_model
        self.client = ZhipuAI(api_key=self.api_key)
        logger.info(f"GLMEmbedding initialized with model: {self.model}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def embed(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed.

        Returns:
            List of floats representing the embedding vector.

        Raises:
            EmbeddingError: If embedding generation fails after retries.
        """
        try:
            logger.debug(f"Generating embedding for text of length: {len(text)}")
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
            )

            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding with dimension: {len(embedding)}")
            return embedding

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise EmbeddingError(f"Embedding generation failed: {e}", cause=e)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts in batch.

        Args:
            texts: List of input texts to embed.

        Returns:
            List of embedding vectors, one for each input text.

        Raises:
            EmbeddingError: If batch embedding generation fails after retries.
        """
        try:
            logger.debug(f"Generating batch embeddings for {len(texts)} texts")
            response = self.client.embeddings.create(
                model=self.model,
                input=texts,
            )

            embeddings = [item.embedding for item in response.data]
            logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings

        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            raise EmbeddingError(f"Batch embedding generation failed: {e}", cause=e)
