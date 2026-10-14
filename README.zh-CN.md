# FD Solutions MCP Server

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Apache](https://img.shields.io/badge/License-Apache%202.0-blue)](https://opensource.org/licenses/Apache-2.0)

[English](README.md) | **简体中文**

面向 [Cursor](https://cursor.com)、[Claude Desktop](https://claude.ai/download)、[Claude Code](https://docs.anthropic.com/en/docs/claude-code)、[VS Code](https://code.visualstudio.com/)（GitHub Copilot / MCP）、[Windsurf](https://windsurf.com/)、[Cline](https://cline.bot/) 等常见 LLM 客户端的 MCP（Model Context Protocol）服务端。通过 **SimWorks FD Solutions** 的 Python API 驱动本机仿真软件。

在已安装 FD Solutions 的机器上，可由 AI 助手完成建模与布局、属性设置、仿真运行与结果分析等操作。

> **说明：** 本仓库只提供 MCP 服务端。`FD Solutions Python API` 随 FD Solutions 产品安装包提供，**不是**本项目的 pip 依赖。

## 功能

- 默认使用 STDIO 传输（适配多数 LLM / MCP 客户端），同时支持 streamable HTTP
- 提供丰富工具，覆盖结构 / 光源 / 监视器的添加与属性设置，以及仿真运行、参数扫描、作业管理等，基本覆盖软件侧常用操作
- 通过环境变量或 `config.json` 指定本机 `FD Solutions Python API` 路径

## 环境要求

- Python **3.10+**
- 已安装 **FD Solutions** 产品
- 有效的 **FD Solutions 产品许可证**

## 安装

```bash
pip install "git+https://github.com/SimWorksSoft/fdsolutions-mcp.git"
```

或克隆后安装：

```bash
git clone https://github.com/SimWorksSoft/fdsolutions-mcp.git
cd fdsolutions-mcp
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# Linux / macOS
# source .venv/bin/activate

pip install -e .
```

## 配置 `FD Solutions Python API` 路径

启动前须能成功 `import simworks`。路径解析顺序：

1. **环境变量**（优先）
   - `FDSOLUTIONS_PYTHON_API`：包含 `simworks.py` 的目录（通常为 `<FD Solutions 安装根>/api/python`）
   - 或 `FDSOLUTIONS_HOME`：FD Solutions 安装根目录（自动使用 `<home>/api/python`）
2. **`config.json`**（环境变量未设置或无效时）
   - 查找顺序：当前工作目录 → 与 `server.py` 同级目录
   - 字段：`python_api_path` — 指向 `<FD Solutions 安装根>/api/python`（相对路径相对于 **config.json 所在目录** 解析）

复制示例文件并按本机路径修改：

```bash
cp config.example.json config.json
```

### 环境变量示例

PowerShell：

```powershell
$env:FDSOLUTIONS_PYTHON_API = "C:\Program Files\SimWorks\SimWorks FD Solutions\api\python"
# 或
$env:FDSOLUTIONS_HOME = "C:\Program Files\SimWorks\SimWorks FD Solutions"
```

bash：

```bash
export FDSOLUTIONS_PYTHON_API="/opt/SimWorks FD Solutions/api/python"
# 或
export FDSOLUTIONS_HOME="/opt/SimWorks FD Solutions"
```

### `config.json` 示例

```json
{
  "python_api_path": "C:/Program Files/SimWorks/SimWorks FD Solutions/api/python"
}
```

产品安装包也可能在 `api/mcp_server/` 下自带相对路径的 `config.json`。开源 / pip 用户建议使用绝对 `python_api_path` 或环境变量。

## 如何运行

默认传输为 **stdio**（推荐用于多数 LLM 客户端）：

```bash
fdsolutions-mcp
```

可选 HTTP 模式：

```bash
fdsolutions-mcp --transport streamable-http --host 127.0.0.1 --port 3001
```

也可在产品安装目录中直接运行：

```bash
cd "<FD Solutions 安装根>/api/mcp_server"
python server.py
python server.py --transport streamable-http --host 127.0.0.1 --port 3001
```

## 在 MCP 客户端中连接

### STDIO（推荐）

由客户端拉起服务进程，示例：

```json
{
  "mcpServers": {
    "fdsolutions": {
      "command": "fdsolutions-mcp",
      "args": [],
      "env": {
        "FDSOLUTIONS_PYTHON_API": "C:/Program Files/SimWorks/SimWorks FD Solutions/api/python"
      }
    }
  }
}
```

若使用虚拟环境，请将 `command` 指向该环境中的 `fdsolutions-mcp`（或对应的 `python` + 脚本路径）。各客户端的配置界面与文件名可能不同，请以对应客户端的 MCP 文档为准。

### HTTP（可选）

```bash
fdsolutions-mcp --transport streamable-http --host 127.0.0.1 --port 3001
```

端点：`http://<host>:<port>/mcp`（默认 `http://127.0.0.1:3001/mcp`）

```json
{
  "mcpServers": {
    "fdsolutions": {
      "url": "http://127.0.0.1:3001/mcp"
    }
  }
}
```

请先启动本 MCP 服务，再在客户端中连接。

## CLI 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--transport` | `stdio` | `stdio` 或 `streamable-http` |
| `--host` | `127.0.0.1` | 监听地址（仅 HTTP） |
| `--port` | `3001` | HTTP 端口（仅 HTTP） |
| `--log-level` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` / `CRITICAL` |

## 许可证

本项目采用 [Apache License 2.0](LICENSE)。

## 免责声明

本 MCP 服务端为配套组件，运行需要本机已安装并完成授权的 FD Solutions。可用能力取决于产品暴露的 Python API，并可能随版本变化。
