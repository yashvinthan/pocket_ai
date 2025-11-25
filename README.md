# POCKET-AI

POCKET-AI is a production-grade, open-source, privacy-first portable assistant that augments (not replaces) the tools you already trust. Voice, vision, wellness nudges, and productivity workflows all run locally on Pi-class hardware and only touch the cloud when you explicitly opt in.

## Highlights
- **Phone Alternative for Productivity** – capture tasks, block calendar time, draft replies, and triage Slack/Email without unlocking your phone.
- **Integration-First** – tasks land in Todoist/Notion, events in Google Calendar, food flows to Swiggy/Zomato, mail drafts into Gmail/Outlook. No new silos.
- **Profiles & Policy Engine** – `OFFLINE_ONLY`, `HYBRID`, or `CUSTOM` determine whether cloud AI is allowed per-operation. Capability checks prevent plugins from overreaching.
- **Secure Storage & Secrets** – encrypted Fernet store for API keys, encrypted TTL-based storage per data category, one-click export + verifiable factory reset.
- **Easy & Dev Modes** – YAML-defined workflows for non-coders, Python plugins with capability declarations for power users.
- **MCP Server** – expose POCKET-AI as a tool provider for Model Context Protocol aware clients (ChatGPT/Claude/Desktop IDEs).

## Quick Start
```bash
git clone https://github.com/<you>/pocket-ai.git
cd pocket-ai
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m pocket_ai
```

To install models and set up services automatically, run `./INSTALL.sh`.

## Configuring Integrations
Routing happens via `config.yaml`:

```yaml
profile: OFFLINE_ONLY
routing:
  task_app: "todoist"
  notes_app: "notion"
  calendar_app: "google_calendar"
  email_app: "gmail"
  chat_app: "slack"
  food_app: "swiggy"
```

Add API tokens with `python -m pocket_ai.cli.secrets set <name>` (or set env vars). Secrets are encrypted at `data/system/secrets.enc`.

## Project Layout
- `pocket_ai/core` – config, profiles, policy engine, secrets, encrypted storage, scheduler.
- `pocket_ai/audio` – wake word, ASR/TTS wrappers, noise suppression, audio buffer.
- `pocket_ai/vision` – camera abstraction, trigger, offline & cloud vision pipes, privacy filter.
- `pocket_ai/ai` – orchestrator, NLU, context manager, local/cloud LLM gateways.
- `pocket_ai/tools` – Easy Mode runtime, plugin registry, dev plugins for Todoist/Notion/GCal/Gmail/Slack/Swiggy/Zomato.
- `pocket_ai/mcp` – Model Context Protocol server exposing assistant_query, run_easy_tool, run_dev_tool, status & data-control.
- `pocket_ai/wellness` – local-only meals/activity/focus logging + nudges.
- `pocket_ai/docs` – privacy, security, data map, hardening, MCP, tool + plugin guides.

## Documentation
- [`docs/PRIVACY.md`](pocket_ai/docs/PRIVACY.md) – privacy defaults, profiles, user rights.
- [`docs/SECURITY.md`](pocket_ai/docs/SECURITY.md) – threat model + mitigations.
- [`docs/DATA_MAP.md`](pocket_ai/docs/DATA_MAP.md) – data categories, retention, export.
- [`docs/MCP.md`](pocket_ai/docs/MCP.md) – how to connect MCP clients.
- [`docs/TOOL_CREATION.md`](pocket_ai/docs/TOOL_CREATION.md) – build Easy Mode workflows.
- [`docs/PLUGIN_DEVELOPMENT.md`](pocket_ai/docs/PLUGIN_DEVELOPMENT.md) – author secure integrations.

## Testing
```bash
pytest tests/test_policy.py
pytest tests/test_storage.py
pytest tests/test_mcp.py
```
Or run the smoke harness: `python tests/verify_basic.py`.

## Privacy & Security
- Offline-first profile enforced by policy engine.
- No hardcoded keys. Secrets encrypted with per-device master key.
- MCP/UI bind to localhost; deploy behind reverse proxy for remote access.
- Factory reset wipes `data/` and regenerates encryption keys.

See `docs/SECURITY.md` and `docs/PRIVACY.md` for the full blueprint.
