# Privacy Profiles

| Profile | Cloud AI | Plugins | Logs |
|---------|----------|---------|------|
| `OFFLINE_ONLY` (default) | `llm`, `vision`, `speech` blocked | Dev plugins allowed, but `network` capability only if integration is local/LAN | Metadata only, auto-pruned |
| `HYBRID` | `llm`, `vision`, `speech` allowed | All registered plugins allowed | Structured logs kept until rotated |
| `CUSTOM` | Overrides via `cloud_overrides` in `config.yaml` | Capabilities decided per plugin | User-defined |

### Configuration Snippet

```yaml
profile: HYBRID
cloud_overrides:
  vision_query: false          # disable GPT-4 Vision even in HYBRID
routing:
  task_app: todoist
  notes_app: notion
  calendar_app: google_calendar
```

Switch profiles through:

- `config.yaml`
- REST API `/config`
- MCP `assistant_profile_set`

Every cloud call passes through `policy_engine.can_use_cloud(operation)` for audit + enforcement.
