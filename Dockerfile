FROM python:3.10-slim-bookworm

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./

# Convert pyproject.toml to requirements and install with pip
RUN pip install --upgrade pip && \
    pip install pyproject-toml && \
    echo "fastapi>=0.115" > requirements.txt && \
    echo "uvicorn[standard]>=0.31" >> requirements.txt && \
    echo "pydantic>=2.5" >> requirements.txt && \
    echo "pydantic-settings>=2.1" >> requirements.txt && \
    echo "typer>=0.9" >> requirements.txt && \
    echo "rich>=13" >> requirements.txt && \
    echo "pypdf2>=3.0" >> requirements.txt && \
    echo "python-docx>=1.1" >> requirements.txt && \
    echo "beautifulsoup4>=4.12" >> requirements.txt && \
    echo "markdown>=3.5" >> requirements.txt && \
    echo "feedparser>=6.0" >> requirements.txt && \
    echo "python-dotenv>=1.0" >> requirements.txt && \
    echo "httpx>=0.27" >> requirements.txt && \
    echo "tenacity>=8.2" >> requirements.txt && \
    echo "notion-client>=2.2" >> requirements.txt && \
    echo "mcp>=1.0" >> requirements.txt && \
    echo "zhipuai>=2.0" >> requirements.txt && \
    echo "tree-sitter>=0.21" >> requirements.txt && \
    echo "chromadb>=0.4.22" >> requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

# If onnxruntime fails to install, try a compatible version
RUN pip install --no-cache-dir --force-reinstall onnxruntime==1.17.1 || \
    pip install --no-cache-dir --force-reinstall onnxruntime==1.16.3 || \
    pip install --no-cache-dir --force-reinstall onnxruntime

# Copy source code
COPY src/ ./src/

# Create data directory
RUN mkdir -p /data/chroma /data/documents

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CHROMA_PERSIST_DIR=/data/chroma
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Run the API server
CMD ["uvicorn", "rag.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
