# POCKET-AI Data Map

Data never leaves the device unless a HYBRID/CUSTOM profile explicitly allows it for a specific request. Each category below corresponds to a `DataLifecycleManager` bucket.

| Category | Storage | TTL | Encrypted | Purpose |
|----------|---------|-----|-----------|---------|
| `audio_buffers` | RAM | 5s | N/A | Wake-word + ASR buffer |
| `image_frames` | RAM | 10s | N/A | On-demand vision capture |
| `transcripts_temp` | Disk (`data/transcripts_temp/`) | 5 min | Yes | Undo/context for recent commands |
| `wellness_logs` | Disk (`data/wellness_logs/`) | 90 days (default) | Yes | Meals/activity/focus summaries |
| `routing_config` | Disk (`data/routing_config/`) | Persistent | Yes | Routing matrix + profile prefs |
| `preferences` | Disk (`data/preferences/`) | Persistent | Yes | UI + device preferences |
| `tokens` | Disk (`data/tokens/`) | Persistent | Yes | OAuth tokens for integrations |

`storage.list_categories()` returns live counts + TTLs for each bucket. The policy engine refuses to persist unknown categories or attempts to store RAM-only data on disk.

## Data Flows

1. **Voice Pipeline** – mic → `audio_buffer` (RAM) → noise suppression → offline ASR. Transcript stored in `transcripts_temp`. Raw samples dropped immediately.
2. **Vision Pipeline** – shutter press → `image_frames` (RAM) → privacy filter → offline MobileNet. Raw frames purged after inference.
3. **Integrations** – orchestrator routes intents to plugins. Only the minimal payload (typically structured JSON) leaves the device; logs capture metadata only.
4. **Wellness** – meal/activity entries logged to `wellness_logs` (encrypted JSON) and optional SQLite (for historical queries).

## Export & Reset

- **Export** – `storage.export_user_data()` bundles selected categories into `data/exports/export_<timestamp>.zip` (contains JSON only). Accessible via MCP `assistant_data_control`.
- **Factory Reset** – removes the entire `data/` directory, deletes encryption keys, recreates clean directories, and reinitialises the storage and secrets managers. After a reset the device contains zero user data.
