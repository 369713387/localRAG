"""RAG system configuration management."""
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """System configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # GLM API configuration
    zhipu_api_key: str = Field(..., description="Zhipu AI API key for main model")
    zhipu_model: str = Field(default="glm-4", description="GLM model name")

    # Embedding model API configuration (can use different API key)
    zhipu_embedding_api_key: Optional[str] = Field(
        default=None, description="Zhipu AI API key for embedding model (falls back to zhipu_api_key)"
    )
    zhipu_embedding_model: str = Field(
        default="embedding-2", description="Embedding model name"
    )

    # ChromaDB configuration
    chroma_persist_dir: Path = Field(
        default=Path("./data/chroma"), description="ChromaDB persistence directory"
    )
    chroma_collection: str = Field(default="documents", description="Collection name")

    # RAG parameters
    chunk_size: int = Field(default=500, description="Document chunk size")
    chunk_overlap: int = Field(default=50, description="Chunk overlap region")
    top_k: int = Field(default=5, description="Number of documents to retrieve")
    max_history: int = Field(default=10, description="Number of conversation turns to keep")

    # API configuration
    api_host: str = Field(default="0.0.0.0", description="API service address")
    api_port: int = Field(default=8000, description="API service port")

    @property
    def chroma_path(self) -> str:
        """Get ChromaDB path as string."""
        return str(self.chroma_persist_dir)

    def get_embedding_api_key(self) -> str:
        """Get the embedding API key, falling back to main API key if not set."""
        return self.zhipu_embedding_api_key or self.zhipu_api_key


# Global configuration instance
settings = Settings()
