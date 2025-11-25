# Developer Plugins

Developer Mode lets you extend POCKET-AI with Python plugins that call into existing services (Todoist, Notion, Slack, Swiggy, etc.). Plugins are sandboxed by the policy engine and only loaded if their capabilities are permitted.

## Anatomy of a Plugin

```python
from pocket_ai.tools.dev_plugins.plugin_base import PluginBase, ToolContext

class TodoistPlugin(PluginBase):
    name = "todoist_tasks"
    description = "Manage tasks in Todoist"
    requires_capabilities = ["network", "secrets:todoist_token"]

    async def execute(self, input_data: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        action = input_data.get("action")
        token = context.secrets.get_secret("todoist_token")
        ...
```

### Capabilities

- `network` – perform outbound HTTP requests (only allowed if the plugin is referenced in the routing matrix).
- `secrets:<name>` – declared when the plugin needs a stored secret. The plugin is only registered if the secret exists.
- `filesystem`, `location`, etc. – see `policy_engine.can_use_capability`.
- `shell` / `camera_raw` – never granted.

### ToolContext

The framework passes a `ToolContext` with:

- `config` – current configuration/routing matrix.
- `policy` – policy engine, in case you need to check additional permissions.
- `secrets` – access to encrypted secrets (`get_secret`, `set_secret`).

## Registering

Drop your plugin file under `pocket_ai/tools/dev_plugins/` and add it to `dev_tools_loader.py`. On startup `tool_registry` checks capabilities; if any are denied, the plugin is skipped with a warning.

## Guidelines

- Keep payloads small and structured—other components (easy tools, MCP) rely on deterministic JSON.
- Never log user content; log metadata only.
- Obey the routing matrix. If the user routes tasks to Notion, don’t auto-create Todoist entries.
- Return `{"status": "success"}` or `{"status": "error", "message": "..."}; orchestrator surfaces these to users.


