"""MCP Server for RAG System - enables Claude Code to query the knowledge base."""
import json
import logging
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default RAG API base URL
DEFAULT_API_BASE = "http://localhost:8000/api/v1"

# Create MCP server instance
server = Server("localrag-mcp")


async def call_rag_api(endpoint: str, method: str = "GET", data: dict | None = None) -> dict:
    """Call the RAG API and return the response.

    Args:
        endpoint: API endpoint path (without /api/v1 prefix)
        method: HTTP method (GET or POST)
        data: Request body data for POST requests

    Returns:
        API response as dictionary
    """
    url = f"{DEFAULT_API_BASE}{endpoint}"
    timeout = httpx.Timeout(30.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        if method == "POST":
            response = await client.post(url, json=data)
        else:
            response = await client.get(url)

        response.raise_for_status()
        return response.json()


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="rag_query",
            description="""Query the RAG knowledge base to get answers based on indexed documents.

Use this tool when you need to search through the user's knowledge base for information
about documents, code, or any content that has been ingested into the system.

Returns an answer along with source documents that were used to generate the response.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The question or search query to find relevant information"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of documents to retrieve (default: 5, max: 20)",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20
                    },
                    "conversation_id": {
                        "type": "string",
                        "description": "Optional conversation ID for multi-turn context"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="rag_list_documents",
            description="""List all documents in the RAG knowledge base.

Returns a list of all documents that have been ingested into the system
with their metadata including document ID, title, source, and creation date.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of documents to return",
                        "default": 50
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Offset for pagination",
                        "default": 0
                    }
                }
            }
        ),
        Tool(
            name="rag_get_stats",
            description="""Get statistics about the RAG knowledge base.

Returns information about:
- Total number of documents
- Collection name
- Storage location
- System status""",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="rag_health_check",
            description="""Check if the RAG API service is running and healthy.

Use this to verify the RAG system is available before making queries.""",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls from Claude Code."""
    try:
        if name == "rag_query":
            query = arguments.get("query", "")
            top_k = arguments.get("top_k", 5)
            conversation_id = arguments.get("conversation_id")

            data = {
                "query": query,
                "top_k": top_k,
            }
            if conversation_id:
                data["conversation_id"] = conversation_id

            result = await call_rag_api("/chat", method="POST", data=data)

            # Format the response
            response_text = f"""**Answer:** {result.get('answer', 'No answer generated')}

**Sources:**
"""
            sources = result.get("sources", [])
            if sources:
                for i, source in enumerate(sources, 1):
                    response_text += f"\n{i}. {source.get('title', 'Untitled')} (Score: {source.get('score', 0):.3f})"
                    response_text += f"\n   ID: {source.get('doc_id', 'unknown')}"
            else:
                response_text += "\nNo sources found."

            if result.get("conversation_id"):
                response_text += f"\n\n**Conversation ID:** {result['conversation_id']}"

            return [TextContent(type="text", text=response_text)]

        elif name == "rag_list_documents":
            limit = arguments.get("limit", 50)
            offset = arguments.get("offset", 0)

            result = await call_rag_api(f"/documents?limit={limit}&offset={offset}")

            documents = result.get("documents", [])
            if not documents:
                return [TextContent(type="text", text="No documents found in the knowledge base.")]

            response_text = f"**Documents in Knowledge Base ({len(documents)} found):**\n\n"
            for i, doc in enumerate(documents, 1):
                response_text += f"{i}. **{doc.get('title', 'Untitled')}**\n"
                response_text += f"   - ID: {doc.get('doc_id', 'unknown')}\n"
                response_text += f"   - Source: {doc.get('source', 'unknown')}\n"
                if doc.get('created_at'):
                    response_text += f"   - Created: {doc['created_at']}\n"
                response_text += "\n"

            return [TextContent(type="text", text=response_text)]

        elif name == "rag_get_stats":
            result = await call_rag_api("/stats")

            response_text = """**RAG Knowledge Base Statistics**

"""
            response_text += f"- **Collection:** {result.get('collection_name', 'unknown')}\n"
            response_text += f"- **Total Documents:** {result.get('document_count', 0)}\n"
            response_text += f"- **Storage Path:** {result.get('persist_directory', 'unknown')}\n"
            response_text += f"- **Status:** {result.get('status', 'unknown')}\n"

            return [TextContent(type="text", text=response_text)]

        elif name == "rag_health_check":
            result = await call_rag_api("/health")

            response_text = f"**RAG API Health Status:** {result.get('status', 'unknown')}\n"
            response_text += f"Version: {result.get('version', 'unknown')}"

            return [TextContent(type="text", text=response_text)]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except httpx.HTTPStatusError as e:
        error_msg = f"API Error: {e.response.status_code} - {e.response.text}"
        logger.error(error_msg)
        return [TextContent(type="text", text=f"Error calling RAG API: {error_msg}")]

    except httpx.ConnectError:
        error_msg = "Cannot connect to RAG API. Make sure the API server is running at " + DEFAULT_API_BASE
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]


async def run_server():
    """Run the MCP server."""
    logger.info("Starting localRAG MCP Server...")
    logger.info(f"Connecting to RAG API at: {DEFAULT_API_BASE}")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def main():
    """Entry point for the MCP server."""
    import asyncio
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
