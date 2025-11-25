# Easy Mode Tool Creation

Easy Mode lets non-developers craft useful workflows with a single YAML file. Tools live in `pocket_ai/tools/easy_definitions/` and are auto-loaded at boot.

## Schema

```yaml
name: "daily_review"
description: "Summarize today's schedule and tasks."
category: "productivity"
input_type: "text"        # "text", "none", ...
output_type: "text"
uses_cloud: false         # set true if GPT fallback required
model: "gpt-4o-mini"      # optional model override
data_sources:
  - plugin: "todoist_tasks"
    as: "tasks_snapshot"
    payload:
      action: "list_open_tasks"
prompt_template: |
  Tasks:
  {{tasks_snapshot}}

  Context:
  {{user_text}}
```

### Fields

- `data_sources` – each entry calls a developer plugin before the prompt is rendered. Results are JSON-encoded and injected via `{{alias}}`.
- `uses_cloud` – if `true`, policy engine must allow the calling profile to use cloud LLMs; otherwise the local GGUF stack is used.
- `allowed_profiles` – optional list to restrict tools to certain profiles.

## Testing

1. Drop your YAML into `pocket_ai/tools/easy_definitions/`.
2. Run `pytest tests/test_mcp.py -k easy_tool` or simply call the tool via MCP.
3. Logs will show prompt + plugin calls if you set `POCKET_LOG_LEVEL=DEBUG`.

## Design Tips

- Keep prompts short; rely on `data_sources` to pull the freshest state from Todoist/Notion/GCal/etc.
- If you need additional context (e.g., wellness trends), add another `data_sources` entry targeting the relevant plugin.
- Prefer `uses_cloud: false` unless you truly need cloud reasoning—offline responses are faster and privacy-friendly.


