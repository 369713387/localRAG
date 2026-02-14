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
