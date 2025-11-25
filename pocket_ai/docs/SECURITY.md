# POCKET-AI Security Architecture

## Threat Model

| Threat | Description | Mitigation | Residual Risk |
|--------|-------------|------------|---------------|
| Lost / Stolen Device | Attacker gains physical access | Full-disk encryption (OS), encrypted data categories, encrypted secrets + factory reset | Hardware-level side-channel attacks |
| Malicious Plugin | Plugin requests more capabilities than necessary | Capability enforcement via `policy_engine`, secrets gating (`secrets:<name>`), routing-based allow-list | User can explicitly enable risky capability in CUSTOM profile |
| Network Attacker | MITM on outbound requests | TLS-only cloud calls, privacy filter before uploads, MCP/UI bind to `127.0.0.1` by default | If user forwards UI without TLS |
| Cloud Compromise | Provider breach (OpenAI, Slack, etc.) | OFFLINE_ONLY default, per-operation consent, privacy filter for images, minimised payloads | Once data leaves device it is subject to provider policies |
| Forensic Recovery | Attempt to recover deleted data | Secure factory reset (delete+recreate storage dir, regenerate keys) | If attacker had root before reset |

## Hardening Checklist

1. **OS Level**
   - Create dedicated `pocketai` user, disable password SSH.
   - Enable UFW: `sudo ufw default deny incoming`, allow only `22` (ssh) and optional reverse-proxy port.
   - Enable automatic security updates (`unattended-upgrades`).
2. **Application Level**
   - Run `pip install -r requirements.txt --require-hashes` for locked deps (future).
   - Secrets via `data/system/secrets.enc` (chmod 600 automatically).
   - Policy engine denies `shell` capability and network use for plugins not referenced in routing.
3. **Network Surface**
   - UI + MCP bind to `127.0.0.1`. Use Nginx/Traefik for remote access with TLS + auth.
   - Cloud calls go through `openai_gateway` which logs every policy decision.
4. **Monitoring**
   - Structured audit logs (metadata only) for policy decisions.
   - Scheduler hook to purge expired data and rotate logs.

## Authentication

- **Device UI**: integrate with OS-level PIN/biometric (outside scope of repo).
- **MCP**: expose via localhost; when remote, terminate TLS + require basic/Bearer auth at proxy.
- **Plugins**: capability gating ensures tokens are only accessible if corresponding `secrets:` capability is authorised *and* the secret exists.

## Secrets Handling

- Never commit secrets. `SecretsManager` encrypts at rest with `secret_master.key`.
- To set a secret: `python -m pocket_ai.cli.secrets set TODOIST_TOKEN`.
- Deleting a secret immediately revokes plugin access (capability check fails).

## Factory Reset

`storage.factory_reset()` removes `data/`, regenerates storage + secret keys, and recreates the directory tree. After a reset there is no linkage to previous data or tokens—users must reconfigure integrations.
