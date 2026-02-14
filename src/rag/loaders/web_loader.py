"""Web内容加载器"""
import logging
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from rag.loaders.base import BaseLoader, Document

logger = logging.getLogger(__name__)


class WebLoader(BaseLoader):
    """Web内容加载器"""

    def __init__(
        self,
        timeout: int = 30,
        user_agent: str = "RAG-Bot/1.0",
        max_content_length: int = 10 * 1024 * 1024,  # 10MB
    ):
        self.timeout = timeout
        self.user_agent = user_agent
        self.max_content_length = max_content_length

    def load(self, source: str) -> list[Document]:
        """加载网页内容"""
        url = source

        if not self._is_valid_url(url):
            raise ValueError(f"无效的URL: {url}")

        content = self._fetch_and_parse(url)

        metadata = {
            "url": url,
            "domain": urlparse(url).netloc,
            "type": "web",
        }

        return [
            Document(
                content=content,
                metadata=metadata,
                source=url,
            )
        ]

    def _is_valid_url(self, url: str) -> bool:
        """验证URL格式"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def _fetch_and_parse(self, url: str) -> str:
        """获取并解析网页"""
        headers = {"User-Agent": self.user_agent}

        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()

            # 检查内容长度
            content_length = len(response.content)
            if content_length > self.max_content_length:
                raise ValueError(f"内容过大: {content_length} bytes")

            return self._parse_html(response.text, url)

    def _parse_html(self, html: str, url: str) -> str:
        """解析HTML提取文本"""
        soup = BeautifulSoup(html, "html.parser")

        # 移除脚本和样式
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        # 获取标题
        title = soup.title.string if soup.title else ""

        # 获取主要内容
        # 尝试找到主要内容区域
        main_content = (
            soup.find("main")
            or soup.find("article")
            or soup.find("div", class_="content")
            or soup.find("body")
        )

        if main_content:
            text = main_content.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)

        # 清理多余空白
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        # 添加标题
        if title:
            clean_text = f"# {title}\n\n{clean_text}"

        return clean_text
