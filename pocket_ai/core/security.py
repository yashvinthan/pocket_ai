from __future__ import annotations

import secrets
from typing import Optional

from pocket_ai.core.secrets_manager import secrets_manager


def verify_token(secret_name: str, provided: Optional[str]) -> bool:
    secret_value = secrets_manager.get_secret(secret_name)
    if not secret_value:
        return False
    if not provided:
        return False
    try:
        return secrets.compare_digest(secret_value, provided)
    except Exception:
        return False

