# INSTALL.md

This file is written for LLM agents and MCP-aware clients. It describes the smallest reliable setup for running this repository as an MCP server.

## 0. What this server provides

- MCP server name suggestion: `kis-mcp-server`
- Runtime: Python 3.13+ with `uv`
- Default transport: `stdio`
- Main entrypoint: `uv run python server.py`
- Tool profiles:
  - `catalog`: 3 tools, recommended for LLM agents to reduce tool-schema context
  - `full`: 15 tools, exposes convenience tools directly
- Trading safety:
  - Order, amend, and cancel APIs are blocked unless `KIS_ENABLE_TRADING=true` is explicitly set.
  - Do not set `KIS_ENABLE_TRADING=true` for read-only account or quote usage.

Recommended LLM default:

```bash
KIS_MCP_TOOLSET=catalog
```

The `catalog` profile still supports all 166 cataloged APIs through `call-kis-api`.

## 1. Prerequisites

Required:

```bash
python --version   # must be 3.13 or newer
uv --version
```

If `uv` is missing:

```bash
pip install uv
```

## 2. Clone and install dependencies

```bash
git clone https://github.com/migusdn/KIS_MCP_Server.git
cd KIS_MCP_Server
uv sync
```

If the repository is already cloned, run only:

```bash
cd <project-root>
uv sync
```

## 3. Create credentials file

Create `.env` from the example:

```bash
cp .env.example .env
chmod 600 .env
```

Edit `.env`:

```bash
KIS_APP_KEY="<app-key>"
KIS_APP_SECRET="<app-secret>"
KIS_ACCOUNT_TYPE="REAL"      # REAL or VIRTUAL
KIS_CANO="<account-first-8-digits>"
KIS_ACNT_PRDT_CD="01"
KIS_MCP_TOOLSET="catalog"    # recommended for LLM agents
KIS_MCP_LOG_LEVEL="WARNING"
```

Notes for LLM agents:

- Never write real credentials into tracked files.
- `.env` and `token.json` must stay untracked.
- Keep `.env` permission at `600` when possible.
- `KIS_TOKEN_FILE` defaults to `token.json`.

## 4. Smoke test locally

Run the server in stdio mode:

```bash
uv run python server.py
```

A stdio MCP server waits for MCP messages, so it may appear idle. Stop it with `Ctrl+C` after confirming it starts.

Optional import/config test:

```bash
uv run python -m compileall main.py server.py example.py tests
uv run python -m unittest discover -v
```

## 5. Tool profile selection

### `catalog` profile: recommended for LLM agents

Use this when the client pays context for every loaded MCP tool schema.

```bash
KIS_MCP_TOOLSET=catalog uv run python server.py
```

Exposed tools:

| Tool | Purpose |
|---|---|
| `list-kis-api-specs` | Search API catalog by group/query |
| `get-kis-api-spec` | Read endpoint, TR_ID candidates, params, labels, examples, values |
| `call-kis-api` | Call any cataloged API by `group`, `api_type`, and `params` |

LLM workflow in `catalog` mode:

1. Use `list-kis-api-specs` to find a candidate API.
2. Use `get-kis-api-spec` to inspect required params and examples.
3. Use `call-kis-api` to execute the API.
4. For state-changing APIs, expect a safety block unless `KIS_ENABLE_TRADING=true` is set.

### `full` profile

Use this when the user wants convenience tools directly visible.

```bash
KIS_MCP_TOOLSET=full uv run python server.py
```

This exposes catalog tools plus convenience tools such as domestic balance, stock price, ask price, and order wrappers.

## 6. Register with Codex CLI

Recommended low-context registration:

```bash
codex mcp add kis-mcp-server \
  --env KIS_MCP_TOOLSET=catalog \
  --env KIS_MCP_LOG_LEVEL=WARNING \
  -- uv --directory <project-root> run python server.py
```

Check registration:

```bash
codex mcp list
codex mcp get kis-mcp-server
```

Remove registration:

```bash
codex mcp remove kis-mcp-server
```

If using the default full toolset, either omit `KIS_MCP_TOOLSET` or set it to `full`.

## 7. Register with Claude Code

Recommended low-context registration:

```bash
claude mcp add kis-mcp-server \
  -e KIS_MCP_TOOLSET=catalog \
  -e KIS_MCP_LOG_LEVEL=WARNING \
  -- uv --directory <project-root> run python server.py
```

Check registration:

```bash
claude mcp list
claude mcp get kis-mcp-server
```

Remove registration:

```bash
claude mcp remove kis-mcp-server
```

Alternative JSON registration for Claude Code:

```bash
claude mcp add-json kis-mcp-server '{
  "type": "stdio",
  "command": "uv",
  "args": ["--directory", "<project-root>", "run", "python", "server.py"],
  "env": {
    "KIS_MCP_TOOLSET": "catalog",
    "KIS_MCP_LOG_LEVEL": "WARNING"
  }
}'
```

## 8. Register with Claude Desktop

Add an MCP server entry to the Claude Desktop configuration file.

Typical macOS path:

```text
~/Library/Application Support/Claude/claude_desktop_config.json
```

Example config:

```json
{
  "mcpServers": {
    "kis-mcp-server": {
      "command": "uv",
      "args": ["--directory", "<project-root>", "run", "python", "server.py"],
      "env": {
        "KIS_MCP_TOOLSET": "catalog",
        "KIS_MCP_LOG_LEVEL": "WARNING"
      }
    }
  }
}
```

Restart Claude Desktop after editing the config.

## 9. Generic MCP client config

Any stdio MCP client can use this shape:

```json
{
  "mcpServers": {
    "kis-mcp-server": {
      "command": "uv",
      "args": ["--directory", "<project-root>", "run", "python", "server.py"],
      "env": {
        "KIS_MCP_TOOLSET": "catalog",
        "KIS_MCP_LOG_LEVEL": "WARNING"
      }
    }
  }
}
```

If the client supports `cwd` but not `uv --directory`, this also works:

```json
{
  "mcpServers": {
    "kis-mcp-server": {
      "command": "uv",
      "args": ["run", "python", "server.py"],
      "cwd": "<project-root>",
      "env": {
        "KIS_MCP_TOOLSET": "catalog",
        "KIS_MCP_LOG_LEVEL": "WARNING"
      }
    }
  }
}
```

## 10. Example LLM calls in `catalog` mode

### Search overseas balance APIs

Tool: `list-kis-api-specs`

```json
{
  "group": "overseas_stock",
  "query": "잔고",
  "limit": 10
}
```

### Inspect overseas stock balance params

Tool: `get-kis-api-spec`

```json
{
  "group": "overseas_stock",
  "api_type": "inquire_balance"
}
```

### Call overseas stock balance

Tool: `call-kis-api`

```json
{
  "group": "overseas_stock",
  "api_type": "inquire_balance",
  "params": {
    "ovrs_excg_cd": "NASD",
    "tr_crcy_cd": "USD"
  }
}
```

### Call overseas buyable amount

Tool: `call-kis-api`

```json
{
  "group": "overseas_stock",
  "api_type": "inquire_psamount",
  "params": {
    "ovrs_excg_cd": "NASD",
    "item_cd": "QQQ",
    "ovrs_ord_unpr": "1"
  }
}
```

### Call domestic stock price

Tool: `call-kis-api`

```json
{
  "group": "domestic_stock",
  "api_type": "inquire_price",
  "params": {
    "fid_cond_mrkt_div_code": "J",
    "fid_input_iscd": "005930"
  }
}
```

## 11. Environment variables

| Name | Required | Default | Description |
|---|---|---|---|
| `KIS_APP_KEY` | yes | - | App key |
| `KIS_APP_SECRET` | yes | - | App secret |
| `KIS_ACCOUNT_TYPE` | yes | - | `REAL` or `VIRTUAL` |
| `KIS_CANO` | for account APIs | - | First 8 digits of account number |
| `KIS_ACNT_PRDT_CD` | for account APIs | `01` | Account product code |
| `KIS_TOKEN_FILE` | no | `token.json` | Token cache path |
| `KIS_ENABLE_TRADING` | no | disabled | Set to `true` only to allow order/amend/cancel APIs |
| `KIS_MCP_TOOLSET` | no | `full` | `catalog` or `full` |
| `KIS_MCP_LOG_LEVEL` | no | `INFO` | Use `WARNING` for quieter MCP clients |
| `MCP_TYPE` | no | `stdio` | `stdio`, `sse`, or `streamable-http` |
| `MCP_HOST` | no | `127.0.0.1` | HTTP/SSE host |
| `MCP_PORT` | no | `8000` | HTTP/SSE port |
| `MCP_PATH` | no | `/mcp` | HTTP/SSE path |

## 12. Troubleshooting

### `uv` cannot find Python 3.13

Install Python 3.13 or configure `uv` to use an available Python 3.13+ interpreter.

### MCP client starts but no tools appear

Check:

```bash
uv --directory <project-root> run python server.py
```

Then verify client registration points to the same `<project-root>`.

### Too many tools are loaded

Set:

```bash
KIS_MCP_TOOLSET=catalog
```

Then restart the MCP client session.

### Account APIs fail with missing credentials

Check `.env` includes:

```bash
KIS_APP_KEY="<app-key>"
KIS_APP_SECRET="<app-secret>"
KIS_ACCOUNT_TYPE="REAL"
KIS_CANO="<account-first-8-digits>"
KIS_ACNT_PRDT_CD="01"
```

### `call-kis-api` rejects a parameter

Use `get-kis-api-spec` and pass parameters by the lowercase `name` field or uppercase `wire_name` field. Unknown parameters are rejected by default.

### Orders are blocked

This is expected unless explicitly enabled:

```bash
KIS_ENABLE_TRADING=true
```

Do not enable this for read-only usage.
