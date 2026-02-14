# localRAG

混合型 RAG（检索增强生成）系统，支持个人知识库管理和代码/技术文档检索。

## 特性

- 多种文档源支持：本地文件（PDF/MD/TXT/DOCX）、代码仓库、Web内容
- 智谱AI GLM 模型集成
- ChromaDB 向量存储
- 多轮对话支持
- CLI 和 REST API 双接口

## 快速开始

### 环境要求

- Python >= 3.10
- Poetry

### 安装

```bash
# 安装依赖
poetry install

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入智谱AI API密钥
```

### CLI 使用

```bash
# 导入文档
poetry run rag ingest ./docs/

# 单次问答
poetry run rag ask "如何配置ChromaDB?"

# 交互式对话
poetry run rag chat

# 查看配置
poetry run rag config

# 查看统计
poetry run rag stats
```

### API 服务

```bash
# 启动API服务
poetry run uvicorn rag.api.main:app --reload

# 访问文档
open http://localhost:8000/docs
```

## 项目结构

```
localRAG/
├── src/rag/
│   ├── core/          # 核心模块 (engine, retriever, chunker)
│   ├── loaders/       # 文档加载器
│   ├── embeddings/    # 向量化
│   ├── storage/       # 向量存储
│   ├── llm/           # LLM客户端
│   ├── memory/        # 对话记忆
│   ├── api/           # REST API
│   └── cli/           # 命令行工具
├── tests/             # 测试
└── data/              # 数据目录
```

## API 接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/v1/documents | 上传文档 |
| GET | /api/v1/documents | 列出文档 |
| DELETE | /api/v1/documents/{id} | 删除文档 |
| POST | /api/v1/chat | 问答 |
| GET | /api/v1/chat/history | 对话历史 |
| GET | /api/v1/health | 健康检查 |
| GET | /api/v1/stats | 系统统计 |

## Claude Code 集成 (MCP)

本项目提供 MCP 服务器，让 Claude Code 可以直接查询你的知识库。

### 快速配置

1. **启动 RAG API 服务**：
```bash
poetry run uvicorn rag.api.main:app --host 0.0.0.0 --port 8000
```

2. **配置 Claude Code MCP**：

编辑 `~/.claude/mcp.json`，添加：
```json
{
  "mcpServers": {
    "localrag": {
      "command": "/path/to/localRAG/.venv/bin/python",
      "args": ["-m", "rag.mcp_server"],
      "cwd": "/path/to/localRAG"
    }
  }
}
```

### 可用工具

| 工具 | 功能 |
|------|------|
| `rag_query` | 查询知识库，获取基于文档的答案 |
| `rag_list_documents` | 列出知识库中的所有文档 |
| `rag_get_stats` | 获取知识库统计信息 |
| `rag_health_check` | 检查 API 服务健康状态 |

详细配置请参考 [docs/mcp-setup.md](docs/mcp-setup.md)。

## 许可证

MIT
