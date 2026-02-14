# NotionLoader 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 localRAG 添加 Notion 数据加载器，支持从 Notion 页面和数据库导入文档。

**Architecture:** 创建 `NotionLoader` 类继承 `BaseLoader`，使用 `notion-client` SDK 调用 Notion API，将 Notion 块转换为 Markdown 格式，支持递归加载子页面。

**Tech Stack:** Python 3.10+, notion-client, pytest

---

## Task 1: 添加依赖

**Files:**
- Modify: `pyproject.toml`
- Modify: `.env.example`

**Step 1: 添加 notion-client 依赖**

在 `pyproject.toml` 的 `[tool.poetry.dependencies]` 部分添加：

```toml
notion-client = "^2.2"
```

**Step 2: 安装依赖**

Run: `poetry install`
Expected: 依赖安装成功

**Step 3: 更新 .env.example**

在 `.env.example` 文件末尾添加：

```bash
# Notion API
NOTION_API_KEY=your_notion_integration_token_here
```

**Step 4: Commit**

```bash
git add pyproject.toml .env.example poetry.lock
git commit -m "chore: add notion-client dependency"
```

---

## Task 2: 创建 NotionLoader 基础结构

**Files:**
- Create: `src/rag/loaders/notion_loader.py`
- Create: `tests/loaders/test_notion_loader.py`

**Step 1: 写失败的测试 - 基础初始化**

创建 `tests/loaders/test_notion_loader.py`：

```python
"""NotionLoader 测试"""
import pytest


class TestNotionLoaderInit:
    """测试 NotionLoader 初始化"""

    def test_init_with_api_key(self):
        """使用显式 API key 初始化"""
        from rag.loaders.notion_loader import NotionLoader

        loader = NotionLoader(api_key="secret_test123")
        assert loader.api_key == "secret_test123"

    def test_init_without_api_key_raises(self, monkeypatch):
        """没有 API key 时抛出异常"""
        from rag.loaders.notion_loader import NotionLoader

        monkeypatch.delenv("NOTION_API_KEY", raising=False)
        with pytest.raises(ValueError, match="NOTION_API_KEY"):
            NotionLoader()

    def test_init_with_env_var(self, monkeypatch):
        """从环境变量读取 API key"""
        from rag.loaders.notion_loader import NotionLoader

        monkeypatch.setenv("NOTION_API_KEY", "secret_env456")
        loader = NotionLoader()
        assert loader.api_key == "secret_env456"
```

**Step 2: 运行测试验证失败**

Run: `poetry run pytest tests/loaders/test_notion_loader.py -v`
Expected: FAIL - Module not found

**Step 3: 实现最小代码**

创建 `src/rag/loaders/notion_loader.py`：

```python
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
```

**Step 4: 运行测试验证通过**

Run: `poetry run pytest tests/loaders/test_notion_loader.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/rag/loaders/notion_loader.py tests/loaders/test_notion_loader.py
git commit -m "feat(notion): add NotionLoader basic structure"
```

---

## Task 3: 实现 ID 提取功能

**Files:**
- Modify: `src/rag/loaders/notion_loader.py`
- Modify: `tests/loaders/test_notion_loader.py`

**Step 1: 写失败的测试 - ID 提取**

在 `tests/loaders/test_notion_loader.py` 添加：

```python
class TestNotionLoaderExtractId:
    """测试 ID 提取"""

    @pytest.fixture
    def loader(self, monkeypatch):
        monkeypatch.setenv("NOTION_API_KEY", "secret_test")
        from rag.loaders.notion_loader import NotionLoader
        return NotionLoader()

    def test_extract_plain_id(self, loader):
        """纯 ID"""
        assert loader._extract_id("abc123def456") == "abc123def456"

    def test_extract_id_with_dashes(self, loader):
        """带连字符的 ID"""
        assert loader._extract_id("abc-123-def-456") == "abc123def456"

    def test_extract_from_notion_page_url(self, loader):
        """notion:// 协议 URL - 页面"""
        result = loader._extract_id("notion://page/abc123def456")
        assert result == "abc123def456"

    def test_extract_from_notion_database_url(self, loader):
        """notion:// 协议 URL - 数据库"""
        result = loader._extract_id("notion://database/xyz789abc")
        assert result == "xyz789abc"

    def test_extract_from_full_url(self, loader):
        """完整 Notion URL"""
        result = loader._extract_id(
            "https://www.notion.so/myworkspace/abc123def456"
        )
        assert result == "abc123def456"

    def test_extract_from_url_with_query(self, loader):
        """带查询参数的 URL"""
        result = loader._extract_id(
            "https://www.notion.so/myworkspace?p=abc123def456"
        )
        assert result == "abc123def456"
```

**Step 2: 运行测试验证失败**

Run: `poetry run pytest tests/loaders/test_notion_loader.py::TestNotionLoaderExtractId -v`
Expected: FAIL - AttributeError: 'NotionLoader' object has no attribute '_extract_id'

**Step 3: 实现 _extract_id 方法**

在 `src/rag/loaders/notion_loader.py` 的 `NotionLoader` 类中添加：

```python
    def _extract_id(self, source: str) -> str:
        """从 URL 或直接 ID 中提取 Notion ID"""
        # 处理 notion:// 协议
        if source.startswith("notion://"):
            path = source.replace("notion://", "")
            # notion://page/xxx 或 notion://database/xxx
            parts = path.split("/")
            if len(parts) >= 2:
                return parts[1].replace("-", "")

        # 处理完整 URL: https://www.notion.so/xxx
        if "notion.so" in source:
            # 带 ?p= 参数的 URL
            if "?p=" in source:
                return source.split("?p=")[1].split("&")[0].replace("-", "")
            # /xxx-ID 格式
            parts = source.split("/")
            last_part = parts[-1].split("?")[0]
            # 提取最后一部分（可能是 ID 或 name-ID 格式）
            if "-" in last_part and len(last_part.split("-")[-1]) >= 32:
                return last_part.split("-")[-1].replace("-", "")
            return last_part.replace("-", "")

        # 纯 ID
        return source.replace("-", "")
```

**Step 4: 运行测试验证通过**

Run: `poetry run pytest tests/loaders/test_notion_loader.py::TestNotionLoaderExtractId -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/rag/loaders/notion_loader.py tests/loaders/test_notion_loader.py
git commit -m "feat(notion): implement ID extraction from various URL formats"
```

---

## Task 4: 实现 Markdown 转换功能

**Files:**
- Modify: `src/rag/loaders/notion_loader.py`
- Modify: `tests/loaders/test_notion_loader.py`

**Step 1: 写失败的测试 - Markdown 转换**

在 `tests/loaders/test_notion_loader.py` 添加：

```python
class TestNotionLoaderMarkdownConversion:
    """测试 Markdown 转换"""

    @pytest.fixture
    def loader(self, monkeypatch):
        monkeypatch.setenv("NOTION_API_KEY", "secret_test")
        from rag.loaders.notion_loader import NotionLoader
        return NotionLoader()

    def test_paragraph_conversion(self, loader):
        """段落转换"""
        blocks = [
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"plain_text": "Hello world"}]
                },
            }
        ]
        result = loader._blocks_to_markdown(blocks)
        assert "Hello world" in result

    def test_heading_conversion(self, loader):
        """标题转换"""
        blocks = [
            {
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"plain_text": "Title"}]
                },
            },
            {
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"plain_text": "Subtitle"}]
                },
            },
        ]
        result = loader._blocks_to_markdown(blocks)
        assert "# Title" in result
        assert "## Subtitle" in result

    def test_list_conversion(self, loader):
        """列表转换"""
        blocks = [
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"plain_text": "Item 1"}]
                },
            },
            {
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [{"plain_text": "Item 2"}]
                },
            },
        ]
        result = loader._blocks_to_markdown(blocks)
        assert "- Item 1" in result
        assert "1. Item 2" in result

    def test_code_block_conversion(self, loader):
        """代码块转换"""
        blocks = [
            {
                "type": "code",
                "code": {
                    "rich_text": [{"plain_text": "print('hello')"}],
                    "language": "python",
                },
            }
        ]
        result = loader._blocks_to_markdown(blocks)
        assert "```python" in result
        assert "print('hello')" in result

    def test_quote_conversion(self, loader):
        """引用转换"""
        blocks = [
            {
                "type": "quote",
                "quote": {
                    "rich_text": [{"plain_text": "A wise quote"}]
                },
            }
        ]
        result = loader._blocks_to_markdown(blocks)
        assert "> A wise quote" in result

    def test_empty_blocks(self, loader):
        """空块列表"""
        result = loader._blocks_to_markdown([])
        assert result == ""
```

**Step 2: 运行测试验证失败**

Run: `poetry run pytest tests/loaders/test_notion_loader.py::TestNotionLoaderMarkdownConversion -v`
Expected: FAIL - AttributeError: 'NotionLoader' object has no attribute '_blocks_to_markdown'

**Step 3: 实现 _blocks_to_markdown 和辅助方法**

在 `src/rag/loaders/notion_loader.py` 的 `NotionLoader` 类中添加：

```python
    def _blocks_to_markdown(self, blocks: list[dict]) -> str:
        """将 Notion 块转换为 Markdown"""
        lines = []

        for block in blocks:
            block_type = block["type"]
            converted = self._convert_block(block, block_type)
            if converted:
                lines.append(converted)
            lines.append("")  # 块间空行

        return "\n".join(lines).strip()

    def _convert_block(self, block: dict, block_type: str) -> str:
        """转换单个块"""
        if block_type == "paragraph":
            text = self._extract_rich_text(block.get("paragraph", {}))
            return text

        elif block_type == "heading_1":
            text = self._extract_rich_text(block.get("heading_1", {}))
            return f"# {text}"

        elif block_type == "heading_2":
            text = self._extract_rich_text(block.get("heading_2", {}))
            return f"## {text}"

        elif block_type == "heading_3":
            text = self._extract_rich_text(block.get("heading_3", {}))
            return f"### {text}"

        elif block_type == "bulleted_list_item":
            text = self._extract_rich_text(block.get("bulleted_list_item", {}))
            return f"- {text}"

        elif block_type == "numbered_list_item":
            text = self._extract_rich_text(block.get("numbered_list_item", {}))
            return f"1. {text}"

        elif block_type == "to_do":
            todo = block.get("to_do", {})
            text = self._extract_rich_text(todo)
            checked = todo.get("checked", False)
            checkbox = "[x]" if checked else "[ ]"
            return f"- {checkbox} {text}"

        elif block_type == "code":
            code = block.get("code", {})
            text = self._extract_rich_text(code)
            lang = code.get("language", "")
            return f"```{lang}\n{text}\n```"

        elif block_type == "quote":
            text = self._extract_rich_text(block.get("quote", {}))
            return f"> {text}"

        elif block_type == "divider":
            return "---"

        elif block_type == "callout":
            callout = block.get("callout", {})
            text = self._extract_rich_text(callout)
            emoji = callout.get("icon", {}).get("emoji", "")
            return f"> {emoji} {text}".strip()

        elif block_type == "child_page":
            title = block.get("child_page", {}).get("title", "子页面")
            return f"[📄 {title}]"

        elif block_type == "image":
            image = block.get("image", {})
            if image.get("type") == "external":
                url = image.get("external", {}).get("url", "")
                return f"![image]({url})"
            return ""

        elif block_type == "bookmark":
            bookmark = block.get("bookmark", {})
            url = bookmark.get("url", "")
            return f"[链接]({url})"

        return ""

    def _extract_rich_text(self, block_data: dict) -> str:
        """从富文本中提取纯文本"""
        rich_text = block_data.get("rich_text", [])
        return "".join(rt.get("plain_text", "") for rt in rich_text)
```

**Step 4: 运行测试验证通过**

Run: `poetry run pytest tests/loaders/test_notion_loader.py::TestNotionLoaderMarkdownConversion -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/rag/loaders/notion_loader.py tests/loaders/test_notion_loader.py
git commit -m "feat(notion): implement Markdown conversion for Notion blocks"
```

---

## Task 5: 实现页面和数据库判断

**Files:**
- Modify: `src/rag/loaders/notion_loader.py`
- Modify: `tests/loaders/test_notion_loader.py`

**Step 1: 写失败的测试 - 判断数据库**

在 `tests/loaders/test_notion_loader.py` 添加：

```python
class TestNotionLoaderIsDatabase:
    """测试数据库判断"""

    def test_is_database_true(self, monkeypatch):
        """是数据库"""
        from unittest.mock import MagicMock
        from rag.loaders.notion_loader import NotionLoader

        monkeypatch.setenv("NOTION_API_KEY", "secret_test")
        loader = NotionLoader()
        loader.client = MagicMock()
        loader.client.databases.retrieve.return_value = {"id": "test"}

        assert loader._is_database("test_id") is True

    def test_is_database_false(self, monkeypatch):
        """不是数据库（是页面）"""
        from unittest.mock import MagicMock
        from rag.loaders.notion_loader import NotionLoader

        monkeypatch.setenv("NOTION_API_KEY", "secret_test")
        loader = NotionLoader()
        loader.client = MagicMock()
        loader.client.databases.retrieve.side_effect = Exception("Not found")

        assert loader._is_database("test_id") is False
```

**Step 2: 运行测试验证失败**

Run: `poetry run pytest tests/loaders/test_notion_loader.py::TestNotionLoaderIsDatabase -v`
Expected: FAIL - AttributeError: 'NotionLoader' object has no attribute '_is_database'

**Step 3: 实现 _is_database 和初始化 client**

修改 `src/rag/loaders/notion_loader.py`：

在文件顶部添加导入：
```python
from notion_client import Client
```

修改 `__init__` 方法：
```python
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
        self.client = Client(auth=self.api_key)
```

添加 `_is_database` 方法：
```python
    def _is_database(self, id: str) -> bool:
        """判断是否为数据库"""
        try:
            self.client.databases.retrieve(database_id=id)
            return True
        except Exception:
            return False
```

**Step 4: 运行测试验证通过**

Run: `poetry run pytest tests/loaders/test_notion_loader.py::TestNotionLoaderIsDatabase -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/rag/loaders/notion_loader.py tests/loaders/test_notion_loader.py
git commit -m "feat(notion): add database detection logic"
```

---

## Task 6: 实现完整的 load 方法

**Files:**
- Modify: `src/rag/loaders/notion_loader.py`
- Modify: `tests/loaders/test_notion_loader.py`

**Step 1: 写失败的测试 - load 方法**

在 `tests/loaders/test_notion_loader.py` 添加：

```python
class TestNotionLoaderLoad:
    """测试 load 方法"""

    def test_load_page(self, monkeypatch):
        """加载页面"""
        from unittest.mock import MagicMock, patch
        from rag.loaders.notion_loader import NotionLoader

        monkeypatch.setenv("NOTION_API_KEY", "secret_test")
        loader = NotionLoader()

        # Mock client
        loader.client = MagicMock()
        loader.client.databases.retrieve.side_effect = Exception("Not a database")
        loader.client.pages.retrieve.return_value = {
            "id": "page123",
            "url": "https://notion.so/page123",
            "created_time": "2024-01-01",
            "last_edited_time": "2024-01-02",
            "properties": {
                "title": {"type": "title", "title": [{"plain_text": "Test Page"}]}
            },
        }
        loader.client.blocks.children.list.return_value = {
            "results": [],
            "has_more": False,
        }

        docs = loader.load("page123")

        assert len(docs) == 1
        assert "Test Page" in docs[0].content
        assert docs[0].metadata["type"] == "notion_page"

    def test_load_database(self, monkeypatch):
        """加载数据库"""
        from unittest.mock import MagicMock
        from rag.loaders.notion_loader import NotionLoader

        monkeypatch.setenv("NOTION_API_KEY", "secret_test")
        loader = NotionLoader()

        # Mock database
        loader.client = MagicMock()
        loader.client.databases.retrieve.return_value = {"id": "db123"}
        loader.client.databases.query.return_value = {
            "results": [
                {
                    "id": "page1",
                    "url": "https://notion.so/page1",
                    "created_time": "2024-01-01",
                    "last_edited_time": "2024-01-01",
                    "properties": {
                        "Name": {"type": "title", "title": [{"plain_text": "Page 1"}]}
                    },
                }
            ],
            "has_more": False,
        }
        loader.client.pages.retrieve.return_value = {
            "id": "page1",
            "url": "https://notion.so/page1",
            "created_time": "2024-01-01",
            "last_edited_time": "2024-01-01",
            "properties": {
                "Name": {"type": "title", "title": [{"plain_text": "Page 1"}]}
            },
        }
        loader.client.blocks.children.list.return_value = {
            "results": [],
            "has_more": False,
        }

        docs = loader.load("db123")

        assert len(docs) >= 1
        assert docs[0].metadata["type"] == "notion_database"
```

**Step 2: 运行测试验证失败**

Run: `poetry run pytest tests/loaders/test_notion_loader.py::TestNotionLoaderLoad -v`
Expected: FAIL - NotImplementedError

**Step 3: 实现完整的 load、_load_page、_load_database 方法**

在 `src/rag/loaders/notion_loader.py` 的 `NotionLoader` 类中替换 `load` 方法并添加新方法：

```python
    def load(self, source: str) -> list[Document]:
        """
        加载 Notion 内容

        Args:
            source: 页面ID、数据库ID、notion:// URL 或完整 Notion URL

        Returns:
            文档列表
        """
        page_id = self._extract_id(source)

        if self._is_database(page_id):
            return self._load_database(page_id)
        else:
            return self._load_page(page_id)

    def _load_page(self, page_id: str, depth: int = 0) -> list[Document]:
        """加载单个页面"""
        if depth > self.max_depth:
            logger.warning(f"达到最大递归深度 {self.max_depth}，跳过子页面")
            return []

        # 获取页面信息
        page = self.client.pages.retrieve(page_id=page_id)
        title = self._get_page_title(page)

        # 获取页面内容块
        blocks = self._get_all_blocks(page_id)
        content = self._blocks_to_markdown(blocks)

        metadata = {
            "type": "notion_database" if depth == 0 and hasattr(self, '_loading_database') else "notion_page",
            "page_id": page_id,
            "title": title,
            "url": page.get("url", ""),
            "created_time": page.get("created_time", ""),
            "last_edited_time": page.get("last_edited_time", ""),
        }

        if depth > 0 or not hasattr(self, '_loading_database'):
            metadata["type"] = "notion_page"

        documents = [
            Document(
                content=f"# {title}\n\n{content}",
                metadata=metadata,
                source=f"notion://page/{page_id}",
            )
        ]

        # 递归加载子页面
        if self.include_children:
            for block in blocks:
                if block["type"] == "child_page":
                    child_id = block["id"]
                    try:
                        documents.extend(self._load_page(child_id, depth + 1))
                    except Exception as e:
                        logger.warning(f"加载子页面失败 {child_id}: {e}")

        return documents

    def _load_database(self, database_id: str) -> list[Document]:
        """加载数据库中的所有页面"""
        self._loading_database = True
        documents = []

        try:
            # 查询数据库所有页面
            response = self.client.databases.query(database_id=database_id)

            for page in response.get("results", []):
                page_id = page["id"]
                try:
                    documents.extend(self._load_page(page_id))
                except Exception as e:
                    logger.warning(f"加载页面失败 {page_id}: {e}")

            # 处理分页
            while response.get("has_more"):
                response = self.client.databases.query(
                    database_id=database_id,
                    start_cursor=response.get("next_cursor"),
                )
                for page in response.get("results", []):
                    page_id = page["id"]
                    try:
                        documents.extend(self._load_page(page_id))
                    except Exception as e:
                        logger.warning(f"加载页面失败 {page_id}: {e}")

        finally:
            delattr(self, '_loading_database')

        return documents

    def _get_all_blocks(self, block_id: str) -> list[dict]:
        """获取所有内容块（含分页）"""
        blocks = []
        response = self.client.blocks.children.list(block_id=block_id)
        blocks.extend(response.get("results", []))

        while response.get("has_more"):
            response = self.client.blocks.children.list(
                block_id=block_id,
                start_cursor=response.get("next_cursor"),
            )
            blocks.extend(response.get("results", []))

        return blocks

    def _get_page_title(self, page: dict) -> str:
        """提取页面标题"""
        properties = page.get("properties", {})

        # 尝试常见的标题属性名
        for key in ["title", "Title", "Name", "名称", "标题"]:
            if key in properties:
                prop = properties[key]
                if prop["type"] == "title" and prop.get("title"):
                    return prop["title"][0]["plain_text"]

        return "Untitled"
```

**Step 4: 运行测试验证通过**

Run: `poetry run pytest tests/loaders/test_notion_loader.py::TestNotionLoaderLoad -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/rag/loaders/notion_loader.py tests/loaders/test_notion_loader.py
git commit -m "feat(notion): implement full page and database loading"
```

---

## Task 7: 更新 loaders __init__.py

**Files:**
- Modify: `src/rag/loaders/__init__.py`

**Step 1: 导出 NotionLoader**

修改 `src/rag/loaders/__init__.py`：

```python
"""数据加载器模块"""
from rag.loaders.base import BaseLoader, Document
from rag.loaders.file_loader import FileLoader
from rag.loaders.code_loader import CodeLoader
from rag.loaders.web_loader import WebLoader
from rag.loaders.notion_loader import NotionLoader

__all__ = [
    "BaseLoader",
    "Document",
    "FileLoader",
    "CodeLoader",
    "WebLoader",
    "NotionLoader",
]
```

**Step 2: 验证导入**

Run: `poetry run python -c "from rag.loaders import NotionLoader; print('OK')"`
Expected: 输出 "OK"

**Step 3: 运行所有测试**

Run: `poetry run pytest tests/loaders/ -v`
Expected: 所有测试通过

**Step 4: Commit**

```bash
git add src/rag/loaders/__init__.py
git commit -m "feat(notion): export NotionLoader from loaders module"
```

---

## Task 8: 最终验证

**Step 1: 运行所有测试**

Run: `poetry run pytest -v`
Expected: 所有测试通过

**Step 2: 类型检查**

Run: `poetry run mypy src/rag/loaders/notion_loader.py --ignore-missing-imports`
Expected: 无错误

**Step 3: 代码格式化**

Run: `poetry run black src/rag/loaders/notion_loader.py tests/loaders/test_notion_loader.py`
Expected: 格式化完成

**Step 4: 最终 commit**

```bash
git add -A
git commit -m "feat(notion): complete NotionLoader implementation with tests"
```

---

## 文件变更汇总

| 文件 | 操作 |
|------|------|
| `pyproject.toml` | 添加 notion-client 依赖 |
| `.env.example` | 添加 NOTION_API_KEY |
| `src/rag/loaders/notion_loader.py` | 新建 |
| `src/rag/loaders/__init__.py` | 导出 NotionLoader |
| `tests/loaders/test_notion_loader.py` | 新建 |

## 使用示例

```bash
# 配置环境变量
export NOTION_API_KEY=secret_xxx

# Python 中使用
from rag.loaders import NotionLoader
loader = NotionLoader()
docs = loader.load("notion://database/YOUR_DATABASE_ID")
```
