"""CLI commands for RAG system."""
import asyncio
import shutil
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from rag.core.config import settings
from rag.core.engine import RAGEngine

app = typer.Typer(name="rag", help="RAG knowledge base management tool")
console = Console()


def get_engine() -> RAGEngine:
    """Get RAG engine instance."""
    from rag.embeddings.glm_embedding import GLMEmbedding
    from rag.storage.chroma_store import ChromaStore
    from rag.llm.glm_client import GLMClient
    from rag.memory.conversation import ConversationMemory
    from rag.core.retriever import Retriever

    embedding = GLMEmbedding()
    store = ChromaStore()
    retriever = Retriever(embedding, store)
    llm = GLMClient()
    memory = ConversationMemory()

    return RAGEngine(retriever, llm, memory)


@app.command()
def ingest(
    source: str = typer.Argument(..., help="Document source path or URL"),
    type: str = typer.Option(
        "auto",
        "--type", "-t",
        help="Document type: auto, file, code, web, notion",
    ),
) -> None:
    """Import documents into the knowledge base.

    Supports file, code, web, and notion document types.
    Displays loading progress and import results.
    """
    # Select loader based on type
    if type == "code":
        from rag.loaders.code_loader import CodeLoader
        loader = CodeLoader()
    elif type == "web":
        from rag.loaders.web_loader import WebLoader
        loader = WebLoader()
    elif type == "notion":
        from rag.loaders.notion_loader import NotionLoader
        loader = NotionLoader()
    elif type == "file" or type == "auto":
        from rag.loaders.file_loader import FileLoader
        loader = FileLoader()
    else:
        console.print(f"[red]Unsupported document type: {type}[/red]")
        raise typer.Exit(1)

    # Load documents
    with console.status("[bold green]Loading documents..."):
        try:
            documents = loader.load(source)
        except FileNotFoundError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]Failed to load documents: {e}[/red]")
            raise typer.Exit(1)

    console.print(f"[green]Successfully loaded {len(documents)} document(s)[/green]")

    if not documents:
        console.print("[yellow]No documents to import[/yellow]")
        return

    # Import to knowledge base
    engine = get_engine()

    async def do_ingest():
        docs_data = [
            {"content": doc.content, "metadata": doc.metadata}
            for doc in documents
        ]
        count = await engine.ingest_documents(docs_data)
        return count

    with console.status("[bold green]Importing to knowledge base..."):
        try:
            count = asyncio.run(do_ingest())
        except Exception as e:
            console.print(f"[red]Failed to import documents: {e}[/red]")
            raise typer.Exit(1)

    console.print(f"[green]Successfully imported {count} document(s) to knowledge base[/green]")


@app.command()
def ask(
    question: str = typer.Argument(..., help="Question to ask"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Number of documents to retrieve"),
) -> None:
    """Ask a single question and get an answer.

    Displays the answer in a panel and shows reference documents in a table.
    """
    engine = get_engine()

    async def do_query():
        return await engine.query(question, top_k=top_k)

    with console.status("[bold green]Thinking..."):
        try:
            result = asyncio.run(do_query())
        except Exception as e:
            console.print(f"[red]Failed to process query: {e}[/red]")
            raise typer.Exit(1)

    # Display answer
    console.print(Panel(result["answer"], title="Answer", border_style="green"))

    # Display sources
    if result["sources"]:
        table = Table(title="Reference Documents")
        table.add_column("Document", style="cyan")
        table.add_column("Relevance", justify="right")

        for source in result["sources"]:
            table.add_row(
                source["title"],
                f"{source['score']:.2f}",
            )

        console.print(table)
    else:
        console.print("[yellow]No reference documents found[/yellow]")


@app.command()
def chat() -> None:
    """Enter interactive chat mode.

    Creates a conversation ID and loops for user input.
    Supports exit commands (exit, quit, q).
    """
    engine = get_engine()

    # Create conversation
    conv_id = engine.memory.create_conversation()

    console.print(Panel(
        "RAG Chat Mode\n\n"
        "Type your questions and press Enter to chat.\n"
        "Type 'exit', 'quit', or 'q' to end the session.",
        title="Welcome",
        style="bold blue"
    ))

    while True:
        try:
            question = Prompt.ask("[bold cyan]You[/bold cyan]")

            if question.lower() in ["exit", "quit", "q"]:
                console.print("[yellow]Goodbye![/yellow]")
                break

            if not question.strip():
                continue

            async def do_query():
                return await engine.query(question, conversation_id=conv_id)

            with console.status("[bold green]Thinking..."):
                try:
                    result = asyncio.run(do_query())
                except Exception as e:
                    console.print(f"[red]Failed to process query: {e}[/red]")
                    continue

            console.print(f"[bold green]Assistant[/bold green]: {result['answer']}")

        except KeyboardInterrupt:
            console.print("\n[yellow]Goodbye![/yellow]")
            break
        except EOFError:
            console.print("\n[yellow]Goodbye![/yellow]")
            break


@app.command("list")
def list_docs() -> None:
    """List indexed documents.

    Displays knowledge base statistics in a table.
    """
    from rag.storage.chroma_store import ChromaStore

    store = ChromaStore()
    stats = store.get_stats()

    table = Table(title="Knowledge Base Statistics")
    table.add_column("Property", style="cyan")
    table.add_column("Value", justify="right")

    table.add_row("Collection Name", stats["collection_name"])
    table.add_row("Document Count", str(stats["document_count"]))
    table.add_row("Storage Path", stats["persist_directory"])

    console.print(table)


@app.command()
def config() -> None:
    """Display current configuration.

    Shows all configuration items in a table.
    """
    table = Table(title="Current Configuration")
    table.add_column("Config Item", style="cyan")
    table.add_column("Value")

    table.add_row("GLM Model", settings.zhipu_model)
    table.add_row("Embedding Model", settings.zhipu_embedding_model)
    table.add_row("ChromaDB Path", str(settings.chroma_persist_dir))
    table.add_row("Chunk Size", str(settings.chunk_size))
    table.add_row("Chunk Overlap", str(settings.chunk_overlap))
    table.add_row("Top-K", str(settings.top_k))
    table.add_row("Max History", str(settings.max_history))
    table.add_row("API Host", settings.api_host)
    table.add_row("API Port", str(settings.api_port))

    console.print(table)


@app.command()
def stats() -> None:
    """Display system statistics.

    Shows document count and other metrics.
    """
    from rag.storage.chroma_store import ChromaStore

    store = ChromaStore()

    table = Table(title="System Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    table.add_row("Total Documents", str(store.count()))

    console.print(table)


@app.command()
def clear() -> None:
    """Clear all data from the knowledge base.

    Requires confirmation before proceeding.
    Deletes all ChromaDB data.
    """
    confirm = typer.confirm(
        "Are you sure you want to clear all data? This action cannot be undone!",
        default=False
    )
    if not confirm:
        console.print("[yellow]Operation cancelled[/yellow]")
        raise typer.Exit()

    from rag.storage.chroma_store import ChromaStore

    # Delete ChromaDB data
    if settings.chroma_persist_dir.exists():
        try:
            shutil.rmtree(settings.chroma_persist_dir)
            console.print("[green]All data has been cleared[/green]")
        except Exception as e:
            console.print(f"[red]Failed to clear data: {e}[/red]")
            raise typer.Exit(1)
    else:
        console.print("[yellow]No data directory found - nothing to clear[/yellow]")


if __name__ == "__main__":
    app()
