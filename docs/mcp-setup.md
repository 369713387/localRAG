# Claude Code MCP 集成指南

本文档说明如何将 localRAG 与 Claude Code 集成，让 Claude 可以查询你的知识库。

## 前提条件

1. 确保 RAG API 服务正在运行：
```bash
poetry run uvicorn rag.api.main:app --host 0.0.0.0 --port 8000
```

2. 确保已导入文档到知识库：
```bash
poetry run rag ingest ./your-docs/
```

## 配置 Claude Code

### 方法 1: 使用配置文件

将 `mcp-config.json` 的内容添加到你的 Claude Code MCP 配置中：

**macOS/Linux:**
```bash
cp mcp-config.json ~/.claude/mcp.json
```

或手动编辑 `~/.claude/mcp.json`：

```json
{
  "mcpServers": {
    "localrag": {
      "command": "poetry",
      "args": ["run", "rag-mcp"],
      "cwd": "/path/to/localRAG",
      "env": {
        "RAG_API_BASE": "http://localhost:8000/api/v1"
      }
    }
  }
}
```

### 方法 2: 使用绝对路径

如果 poetry 不在 PATH 中，使用绝对路径：

```json
{
  "mcpServers": {
    "localrag": {
      "command": "/path/to/localRAG/.venv/bin/python",
      "args": ["-m", "rag.mcp_server"],
      "cwd": "/path/to/localRAG",
      "env": {
        "RAG_API_BASE": "http://localhost:8000/api/v1"
      }
    }
  }
}
```

## 可用工具

配置完成后，Claude Code 将可以使用以下工具：

### 1. `rag_query` - 查询知识库

```
查询 RAG 知识库，基于已索引的文档获取答案。
```

参数：
- `query` (必需): 问题或搜索查询
- `top_k` (可选): 返回文档数量，默认 5
- `conversation_id` (可选): 多轮对话 ID

### 2. `rag_list_documents` - 列出文档

```
列出知识库中的所有文档。
```

### 3. `rag_get_stats` - 获取统计

```
获取知识库统计信息。
```

### 4. `rag_health_check` - 健康检查

```
检查 RAG API 服务是否正常运行。
```

## 使用示例

在 Claude Code 中，你可以这样使用：

```
用户: 帮我查一下知识库里关于 ChromaDB 配置的信息

Claude: [调用 rag_query 工具]
根据知识库中的文档，ChromaDB 的配置方式是...
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `RAG_API_BASE` | `http://localhost:8000/api/v1` | RAG API 基础 URL |

## 故障排除

### MCP 服务器无法启动

1. 确保已安装依赖：
```bash
poetry install
```

2. 手动测试 MCP 服务器：
```bash
poetry run rag-mcp
```

### 无法连接到 RAG API

1. 检查 API 服务是否运行：
```bash
curl http://localhost:8000/api/v1/health
```

2. 检查端口是否被占用：
```bash
lsof -i :8000
```

### 查询返回空结果

确保已导入文档：
```bash
poetry run rag stats
```
