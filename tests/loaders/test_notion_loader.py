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
