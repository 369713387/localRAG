# NotionLoader 设计文档

## 概述

为 localRAG 系统添加 Notion 内容加载器，支持从 Notion 页面和数据库批量导入文档到 RAG 系统。

## 需求

- 支持加载单个 Notion 页面
- 支持加载 Notion 数据库（批量加载多个条目）
- 递归加载所有子页面
- 支持多种输入格式（notion:// 协议、完整 URL、纯 ID）
- 将 Notion 富文本块转换为 Markdown 格式

## 架构

### 类结构

```
NotionLoader(BaseLoader)
├── __init__(api_key, include_children, max_depth)
├── load(source) -> list[Document]        # 主入口
├── _extract_id(source) -> str            # 提取/规范化 ID
├── _is_database(id) -> bool              # 判断是否为数据库
├── _load_page(page_id, depth)            # 加载单个页面
├── _load_database(database_id)           # 加载数据库
├── _get_all_blocks(block_id)             # 获取所有内容块（含分页）
├── _get_page_title(page) -> str          # 提取页面标题
└── _blocks_to_markdown(blocks) -> str    # 转换为 Markdown
```

### 数据流

```
输入源 (ID/URL)
    ↓
_extract_id() → 规范化的 Notion ID
    ↓
_is_database() → 判断类型
    ↓
┌─────────────────┬─────────────────┐
│   数据库        │     页面        │
│ _load_database()│   _load_page()  │
└─────────────────┴─────────────────┘
    ↓                    ↓
    Notion API 调用 + 递归子页面
    ↓
_blocks_to_markdown() → Markdown 文本
    ↓
Document 对象列表
```

## 输入格式支持

| 格式 | 示例 |
|------|------|
| notion:// 协议 | `notion://page/abc123`, `notion://database/xyz789` |
| 完整 URL | `https://www.notion.so/workspace/abc123` |
| 带 p 参数的 URL | `https://www.notion.so/workspace?page=abc123` |
| 纯 ID | `abc123def456` 或 `abc123-def4-56gh` |

## 支持的 Notion 块类型

| 块类型 | Markdown 输出 |
|--------|--------------|
| paragraph | 纯文本 |
| heading_1/2/3 | `#` / `##` / `###` |
| bulleted_list_item | `- item` |
| numbered_list_item | `1. item` |
| to_do | `- [ ]` 或 `- [x]` |
| code | ` ```lang\ncode\n``` ` |
| quote | `> text` |
| callout | `> emoji text` |
| divider | `---` |
| child_page | 递归加载 |
| image | `![alt](url)` |
| bookmark | `[title](url)` |

## 配置

### 环境变量

```bash
# .env
NOTION_API_KEY=secret_xxx
```

### 初始化参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| api_key | str \| None | None | Notion Integration Token，未提供时从环境变量读取 |
| include_children | bool | True | 是否递归加载子页面 |
| max_depth | int | 5 | 最大递归深度，防止无限嵌套 |

## 依赖

```toml
[tool.poetry.dependencies]
notion-client = "^2.0"
```

## 文件变更

| 文件 | 操作 |
|------|------|
| `src/rag/loaders/notion_loader.py` | 新建 |
| `src/rag/loaders/__init__.py` | 修改，导出 NotionLoader |
| `pyproject.toml` | 修改，添加 notion-client 依赖 |
| `.env.example` | 修改，添加 NOTION_API_KEY |

## 使用示例

```python
from rag.loaders import NotionLoader

loader = NotionLoader()

# 加载数据库
docs = loader.load("notion://database/abc123")

# 加载页面（含子页面）
docs = loader.load("https://www.notion.so/workspace/xyz789")

# 仅加载顶层页面
loader = NotionLoader(include_children=False)
docs = loader.load("xyz789")
```

## CLI 集成

```bash
# 导入 Notion 数据库
poetry run rag ingest "notion://database/YOUR_DATABASE_ID"

# 导入 Notion 页面
poetry run rag ingest "https://www.notion.so/xxx?p=PAGE_ID"
```

## 错误处理

- API Key 未配置：抛出 `ValueError`
- 无效的 ID/URL：抛出 `ValueError`
- API 调用失败：捕获并记录日志，跳过该项继续处理
- 递归深度超限：停止递归，记录警告

## 测试计划

1. 单元测试：ID 提取、Markdown 转换
2. 集成测试：页面加载、数据库加载、子页面递归
3. 边界测试：空页面、深度限制、无效 ID
