"""Notion内容加载器"""
import logging
import os

from rag.loaders.base import BaseLoader, Document

logger = logging.getLogger(__name__)


class NotionLoader(BaseLoader):
    """Notion页面和数据库加载器"""

    def __init__(
        self,
        api_key: str | None = None,
        include_children: bool = True,
        max_depth: int = 5,
    ):
        self.api_key = api_key or os.getenv("NOTION_API_KEY")
        if not self.api_key:
            raise ValueError("需要提供 NOTION_API_KEY")

        self.include_children = include_children
        self.max_depth = max_depth

    def load(self, source: str) -> list[Document]:
        """加载 Notion 内容"""
        raise NotImplementedError("待实现")
