"""代码仓库加载器"""
import logging
from pathlib import Path

from rag.loaders.base import BaseLoader, Document

logger = logging.getLogger(__name__)


class CodeLoader(BaseLoader):
    """代码仓库加载器"""

    # 常见代码文件扩展名
    CODE_EXTENSIONS = {
        ".py", ".js", ".ts", ".jsx", ".tsx",
        ".go", ".java", ".kt", ".rs", ".cpp", ".c", ".h",
        ".rb", ".php", ".swift", ".scala",
        ".sh", ".bash", ".zsh",
    }

    # 需要忽略的目录
    IGNORE_DIRS = {
        "node_modules", "venv", ".venv", "__pycache__",
        ".git", ".github", "dist", "build", "target",
        "vendor", ".idea", ".vscode",
    }

    def __init__(
        self,
        max_file_size: int = 100 * 1024,  # 100KB
        include_comments: bool = True,
    ):
        self.max_file_size = max_file_size
        self.include_comments = include_comments

    def load(self, source: str) -> list[Document]:
        """加载代码文件或目录"""
        path = Path(source)

        if not path.exists():
            raise FileNotFoundError(f"路径不存在: {source}")

        if path.is_file():
            return [self._load_file(path)]
        elif path.is_dir():
            return self._load_directory(path)
        else:
            raise ValueError(f"不支持的路径类型: {source}")

    def _load_file(self, file_path: Path) -> Document:
        """加载单个代码文件"""
        content = file_path.read_text(encoding="utf-8")

        # 构建带语言标识的内容
        lang = self._get_language(file_path.suffix)
        formatted_content = f"```{lang}\n{content}\n```"

        metadata = self._get_file_metadata(file_path)
        metadata["language"] = lang
        metadata["type"] = "code"

        return Document(
            content=formatted_content,
            metadata=metadata,
            source=str(file_path),
        )

    def _load_directory(self, dir_path: Path) -> list[Document]:
        """加载代码目录"""
        documents = []

        for file_path in dir_path.rglob("*"):
            # 跳过忽略目录
            if any(part in self.IGNORE_DIRS for part in file_path.parts):
                continue

            # 只处理代码文件
            if file_path.suffix.lower() not in self.CODE_EXTENSIONS:
                continue

            # 跳过大文件
            if file_path.stat().st_size > self.max_file_size:
                logger.debug(f"跳过大文件: {file_path}")
                continue

            try:
                doc = self._load_file(file_path)
                documents.append(doc)
            except Exception as e:
                logger.warning(f"加载代码文件失败 {file_path}: {e}")

        return documents

    def _get_language(self, ext: str) -> str:
        """根据扩展名获取语言标识"""
        mapping = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "jsx",
            ".tsx": "tsx",
            ".go": "go",
            ".java": "java",
            ".kt": "kotlin",
            ".rs": "rust",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".scala": "scala",
            ".sh": "bash",
            ".bash": "bash",
        }
        return mapping.get(ext.lower(), "text")
