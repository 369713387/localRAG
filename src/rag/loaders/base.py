"""加载器基类"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Generator


@dataclass
class Document:
    """文档数据类"""

    content: str
    metadata: dict
    source: str


class BaseLoader(ABC):
    """加载器基类"""

    @abstractmethod
    def load(self, source: str) -> list[Document]:
        """
        加载文档

        Args:
            source: 文档源(路径/URL等)

        Returns:
            文档列表
        """
        pass

    def load_generator(self, source: str) -> Generator[Document, None, None]:
        """生成器版本的加载方法"""
        yield from self.load(source)

    def _get_file_metadata(self, file_path: Path) -> dict:
        """获取文件元数据"""
        stat = file_path.stat()
        return {
            "filename": file_path.name,
            "extension": file_path.suffix,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "path": str(file_path),
        }
