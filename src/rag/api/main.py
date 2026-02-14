"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rag.api.routes import chat, documents, system
from rag.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle manager.

    Handles startup and shutdown events for the FastAPI application.
    """
    # Startup
    print("RAG API starting up...")
    print(f"API will be available at http://{settings.api_host}:{settings.api_port}")
    yield
    # Shutdown
    print("RAG API shutting down...")


app = FastAPI(
    title="RAG API",
    description="RAG Knowledge Base API Service",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers with API v1 prefix
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(system.router, prefix="/api/v1", tags=["system"])


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    """Root endpoint returning API information."""
    return {"message": "RAG API", "version": "0.1.0"}
