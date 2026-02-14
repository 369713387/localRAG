FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy source code
COPY src/ ./src/

# Create data directory
RUN mkdir -p /data/chroma /data/documents

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CHROMA_PERSIST_DIR=/data/chroma

# Run the API server
CMD ["uvicorn", "rag.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
