# Model Context Protocol (MCP) Server

POCKET-AI exposes a first-class MCP server so desktop agents (Claude Desktop, Cursor, IDE copilots) can reuse the device as a privacy-preserving tool provider.

## Connection

- **Transport**: HTTP(S) / Server-Sent Events
- **Host**: `127.0.0.1`
- **Port**: `8000`
- **Authentication**: Bind to localhost; for remote exposure place behind a reverse proxy with TLS + auth.

## Available Tools

| Tool | Description |
|------|-------------|
| `assistant_query` | Send natural language commands → orchestrator. |
| `run_easy_tool` | Execute an Easy Mode workflow (`tool_name`, optional payload). |
| `run_dev_tool` | Call a registered plugin directly (`plugin`, `payload`). |
| `assistant_status` | Inspect current profile, connectivity, routing matrix, enabled integrations. |
| `assistant_profile_set` | Switch privacy profile (`OFFLINE_ONLY`, `HYBRID`, `CUSTOM`). |
| `assistant_data_control` | List/export/delete categories or trigger a factory reset. |
| `list_tools` | Enumerate available easy/dev tools. |

Example payload:

```json
{
  "name": "run_easy_tool",
  "arguments": {
    "tool_name": "daily_review",
    "payload": {}
  }
}
```

## Sample Workflows

- **Query**: `assistant_query` with `"Add 'call Arjun about invoice on Friday' to my tasks"` → orchestrator routes to Todoist plugin.
- **Easy Mode**: `run_easy_tool` for `daily_review` to generate a quick wrap-up for the day.
- **Data Export**: `assistant_data_control` with `{"operation": "export"}` returns the path to an encrypted ZIP bundle of user data.

Full schema definitions live in `pocket_ai/mcp/server.py`.
