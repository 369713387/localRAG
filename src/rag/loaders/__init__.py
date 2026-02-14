"""数据加载器模块"""
from rag.loaders.base import BaseLoader, Document
from rag.loaders.file_loader import FileLoader
from rag.loaders.code_loader import CodeLoader
from rag.loaders.web_loader import WebLoader

__all__ = [
    "BaseLoader",
    "Document",
    "FileLoader",
    "CodeLoader",
    "WebLoader",
]
