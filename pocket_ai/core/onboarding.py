from __future__ import annotations

import json
import secrets
import sys
from pathlib import Path
from typing import Dict, Optional

import yaml

from pocket_ai.core.config import get_config, load_config
from pocket_ai.core.logger import logger
from pocket_ai.core.secrets_manager import secrets_manager


def run_first_boot_setup():
    state = get_onboarding_state()
    if state:
        if state.get("pending_ack"):
            print(
                "\nOnboarding is waiting for confirmation. Visit /onboarding?code="
                f"{state.get('setup_code')} to review your tokens.\n"
            )
        return

    cfg = get_config()
    flag_path = _state_path(cfg.storage_path)

    interactive = sys.stdin.isatty()
    print("\n=== Pocket AI First-Time Setup ===")
    print("We will collect a few preferences to lock down the device.\n")

    profile = _prompt(
        "Choose privacy profile [OFFLINE_ONLY/HYBRID/CUSTOM]",
        default="OFFLINE_ONLY",
        interactive=interactive,
    )
    allowed_origin = _prompt(
        "Enter trusted UI origin", default="http://localhost", interactive=interactive
    )

    api_token = _provision_token("api_auth_token", "API client", interactive)
    mcp_token = _provision_token("mcp_auth_token", "MCP client", interactive)
    setup_code = secrets.token_urlsafe(16)

    _persist_config(profile, allowed_origin)
    state_payload = {
        "profile": profile,
        "allowed_origin": allowed_origin,
        "api_token": api_token,
        "mcp_token": mcp_token,
        "setup_code": setup_code,
        "pending_ack": True,
    }
    flag_path.write_text(json.dumps(state_payload, indent=2), encoding="utf-8")
    logger.info("First-time setup complete. Store the printed credentials securely.")
    print("\nSetup complete. Keep these tokens safe:")
    print(f"- API token: {api_token}")
    print(f"- MCP token: {mcp_token}\n")
    print(f"Need a GUI? Visit http://localhost:8000/onboarding?code={setup_code}\n")
    load_config()  # reload config with new values


def get_onboarding_state() -> Optional[Dict]:
    cfg = get_config()
    flag_path = _state_path(cfg.storage_path)
    if not flag_path.exists():
        return None
    try:
        return json.loads(flag_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def acknowledge_onboarding(code: str) -> bool:
    state = get_onboarding_state()
    if not state or not state.get("pending_ack"):
        return False
    if state.get("setup_code") != code:
        return False

    state["pending_ack"] = False
    state.pop("api_token", None)
    state.pop("mcp_token", None)
    state.pop("setup_code", None)
    _state_path(get_config().storage_path).write_text(json.dumps(state, indent=2), encoding="utf-8")
    logger.info("Onboarding acknowledged via GUI flow.")
    return True


def _prompt(message: str, default: str, interactive: bool) -> str:
    if not interactive:
        return default
    value = input(f"{message} [{default}]: ").strip()
    return value or default


def _provision_token(secret_name: str, label: str, interactive: bool) -> str:
    existing = secrets_manager.get_secret(secret_name)
    if existing:
        return existing
    token = (
        input(f"Enter {label} token (leave blank to auto-generate): ").strip()
        if interactive
        else ""
    )
    if not token:
        token = secrets.token_urlsafe(32)
    secrets_manager.set_secret(secret_name, token)
    return token


def _persist_config(profile: str, allowed_origin: str):
    config_path = Path("config.yaml")
    config_data: Dict = {}
    if config_path.exists():
        config_data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}

    config_data["profile"] = profile
    api_block = config_data.setdefault("api", {})
    api_block["allowed_origins"] = [allowed_origin]
    api_block["bind_host"] = api_block.get("bind_host", "127.0.0.1")
    api_block["require_auth"] = True

    config_path.write_text(yaml.safe_dump(config_data, sort_keys=False), encoding="utf-8")


def _state_path(storage_path: str) -> Path:
    return Path(storage_path) / "system" / "onboarding_complete.json"

