"""Notion内容加载器"""
import logging
import os

from notion_client import Client

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
        self.client = Client(auth=self.api_key)

    def _is_database(self, id: str) -> bool:
        """判断是否为数据库"""
        try:
            self.client.databases.retrieve(database_id=id)
            return True
        except Exception:
            return False

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
