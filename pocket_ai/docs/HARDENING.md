# POCKET-AI Hardening Guide

## 1. OS Security
- Run the stack as a dedicated `pocketai` user (never root).
- Disable password SSH, rely on keys, and enable `ufw` (`deny incoming`, allow SSH + proxy port only).
- Install `unattended-upgrades` for automatic patching.

## 2. Application Security
- Secrets live in `data/system/secrets.enc` (Fernet). Protect `secret_master.key` with `chmod 600`.
- Services bind to `127.0.0.1`; terminate TLS + authentication at an external proxy when exposing remotely.
- Policy engine denies dangerous capabilities (`shell`, `camera_raw`) and only enables `network` for integrations referenced in `config.yaml`.

## 3. Physical Security
- Enable full-disk encryption (LUKS) on the Pi/SSD.
- Disable unused USB ports where possible and use tamper-evident seals for production devices.

## 4. Updates
- Run `apt update && apt upgrade` regularly.
- Update Python deps via `pip install -U -r requirements.txt`.
- Rotate API keys/refresh tokens every 90 days via `python -m pocket_ai.cli.secrets`.
