# POCKET-AI Privacy Manifesto

POCKET-AI treats your data as something to protect, not monetise. The system ships with `OFFLINE_ONLY` enabled, never sends raw media off-device, and gives you clear controls to review, export, or delete *everything*.

## Operating Profiles

| Profile | Cloud AI | Integrations | Logging |
|---------|----------|--------------|---------|
| `OFFLINE_ONLY` (default) | Disabled for LLM/Vision/Speech | Local network plugins only | Metadata only (no content) |
| `HYBRID` | Allowed for specific operations (`llm`, `vision`, `speech`) | All enabled integrations | Structured logs for troubleshooting |
| `CUSTOM` | User-defined per-operation | User-defined | User-defined |

Switch profiles via `config.yaml`, the device UI, or the MCP `assistant_profile_set` tool.

## Data Lifecycle

See [`DATA_MAP.md`](DATA_MAP.md) for the exhaustive table. Highlights:

- **Audio / Image Buffers** – RAM only, auto-cleared within seconds.
- **Transcripts** – `transcripts_temp` encrypted, 5-minute TTL.
- **Wellness Logs** – Encrypted, 90-day retention (configurable).
- **Routing Config / Preferences / Tokens** – Encrypted, kept until factory reset.
- **Exports** – Produced on-demand as encrypted ZIP bundles.

Every write goes through `policy_engine.can_persist` to enforce TTL + minimisation.

## Secrets & Integrations

- Secrets live in `data/system/secrets.enc` (Fernet encrypted with per-device key).
- No secrets in git; tests fail if detected.
- Integrations only activate if referenced in the routing matrix.

## User Rights

- **Access** – `MCP assistant_data_control` (`list_categories`, `export`).
- **Deletion** – `assistant_data_control` with `delete` or `factory_reset`.
- **Portability** – Export bundle (JSON inside ZIP).
- **Forget Me** – Factory reset wipes `data/` and regenerates encryption keys.

## Telemetry

POCKET-AI sends **zero telemetry**. Logs stay on-device, metadata-only, and auto-expire in OFFLINE_ONLY mode.
