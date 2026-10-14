# FD Solutions MCP Server

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Apache](https://img.shields.io/badge/License-Apache%202.0-blue)](https://opensource.org/licenses/Apache-2.0)

**English** | [简体中文](README.zh-CN.md)

MCP (Model Context Protocol) server for common LLM clients such as [Cursor](https://cursor.com), [Claude Desktop](https://claude.ai/download), [Claude Code](https://docs.anthropic.com/en/docs/claude-code), [VS Code](https://code.visualstudio.com/) (GitHub Copilot / MCP), [Windsurf](https://windsurf.com/), and [Cline](https://cline.bot/). It drives the local simulation software through the **SimWorks FD Solutions** Python API.

On a machine with FD Solutions installed, an AI assistant can handle modeling and layout, property setup, running simulations, and analyzing results.

> **Note:** This repository provides the MCP server only. The `FD Solutions Python API` ships with the FD Solutions product install and is **not** a pip dependency of this project.

## Features

- STDIO transport by default (works with most LLM / MCP clients), with optional streamable HTTP
- Broad tool coverage for adding and configuring structures, sources, and monitors, plus running simulations, parameter sweeps, job management, and other common product workflows
- Locate the local `FD Solutions Python API` via environment variables or `config.json`

## Requirements

- Python **3.10+**
- The **FD Solutions** product installed
- A valid **FD Solutions product license**

## Installation

```bash
pip install "git+https://github.com/SimWorksSoft/fdsolutions-mcp.git"
```

Or clone and install:

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

## Configure the `FD Solutions Python API` path

Before start-up the server must be able to `import simworks`. Resolution order:

1. **Environment variables** (highest priority)
   - `FDSOLUTIONS_PYTHON_API` — directory that contains `simworks.py` (usually `<FD Solutions install root>/api/python`)
   - or `FDSOLUTIONS_HOME` — FD Solutions install root (uses `<home>/api/python`)
2. **`config.json`** if env is unset or invalid
   - Search order: current working directory → directory next to `server.py`
   - Field: `python_api_path` — path to `<FD Solutions install root>/api/python` (relative paths are resolved against the **directory of `config.json`**)

Copy the example file and edit it for your machine:

```bash
cp config.example.json config.json
```

### Environment examples

PowerShell:

```powershell
$env:FDSOLUTIONS_PYTHON_API = "C:\Program Files\SimWorks\SimWorks FD Solutions\api\python"
# or
$env:FDSOLUTIONS_HOME = "C:\Program Files\SimWorks\SimWorks FD Solutions"
```

bash:

```bash
export FDSOLUTIONS_PYTHON_API="/opt/SimWorks FD Solutions/api/python"
# or
export FDSOLUTIONS_HOME="/opt/SimWorks FD Solutions"
```

### `config.json` example

```json
{
  "python_api_path": "C:/Program Files/SimWorks/SimWorks FD Solutions/api/python"
}
```

Product installs may also ship a `config.json` under `api/mcp_server/` with a relative path. Open-source / pip users should prefer an absolute `python_api_path` or environment variables.

## How to run

Default transport is **stdio** (recommended for most LLM clients):

```bash
fdsolutions-mcp
```

Optional HTTP mode:

```bash
fdsolutions-mcp --transport streamable-http --host 127.0.0.1 --port 3001
```

You can also run from a product install tree:

```bash
cd "<FD Solutions install root>/api/mcp_server"
python server.py
python server.py --transport streamable-http --host 127.0.0.1 --port 3001
```

## Connect from an MCP client

### STDIO (recommended)

Let the client spawn the server process. Example:

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

If you use a virtual environment, point `command` at that environment’s `fdsolutions-mcp` (or the matching `python` + script path). Exact config UI and file names vary by client — follow your client’s MCP documentation.

### HTTP (optional)

```bash
fdsolutions-mcp --transport streamable-http --host 127.0.0.1 --port 3001
```

Endpoint: `http://<host>:<port>/mcp` (default `http://127.0.0.1:3001/mcp`)

```json
{
  "mcpServers": {
    "fdsolutions": {
      "url": "http://127.0.0.1:3001/mcp"
    }
  }
}
```

Start this MCP server first, then connect from the client.

## CLI options

| Option | Default | Description |
|--------|---------|-------------|
| `--transport` | `stdio` | `stdio` or `streamable-http` |
| `--host` | `127.0.0.1` | Bind address (HTTP only) |
| `--port` | `3001` | HTTP port (HTTP only) |
| `--log-level` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` / `CRITICAL` |

## License

This project is licensed under the [Apache License 2.0](LICENSE).

## Disclaimer

This MCP server is a companion component and requires a local, licensed FD Solutions installation. Available capabilities follow the product’s exposed Python API and may change across releases.
