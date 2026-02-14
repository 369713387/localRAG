"""RAG system exception definitions."""


class RAGError(Exception):
    """RAG base exception."""

    def __init__(self, message: str, cause: Exception | None = None):
        self.message = message
        self.cause = cause
        super().__init__(self.message)


class DocumentLoadError(RAGError):
    """Document loading failed."""

    pass


class EmbeddingError(RAGError):
    """Embedding generation failed."""

    pass


class RetrievalError(RAGError):
    """Retrieval failed."""

    pass


class LLMError(RAGError):
    """LLM call failed."""

    pass


class ConfigurationError(RAGError):
    """Configuration error."""

    pass
