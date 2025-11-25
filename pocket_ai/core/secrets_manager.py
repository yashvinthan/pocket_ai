from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional

from cryptography.fernet import Fernet

from pocket_ai.core.config import get_config
from pocket_ai.core.logger import logger


class SecretsManager:
    """
    Encrypts user/API secrets at rest and offers a simple rotation API.
    """

    def __init__(self):
        self.config = get_config()
        self.base_dir = Path(self.config.storage_path) / "system"
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self._key_path = self.base_dir / "secret_master.key"
        self._secrets_path = self.base_dir / "secrets.enc"
        self._cipher = Fernet(self._load_or_create_key())
        self._secrets: Dict[str, str] = self._load_store()

    def _load_or_create_key(self) -> bytes:
        if key_override := os.environ.get("POCKET_MASTER_KEY"):
            return key_override.encode()
        if self._key_path.exists():
            return self._key_path.read_bytes()
        key = Fernet.generate_key()
        self._key_path.write_bytes(key)
        os.chmod(self._key_path, 0o600)
        return key

    def _load_store(self) -> Dict[str, str]:
        if not self._secrets_path.exists():
            return {}
        try:
            decrypted = self._cipher.decrypt(self._secrets_path.read_bytes())
            return json.loads(decrypted.decode("utf-8"))
        except Exception as exc:
            logger.error(f"Failed to load secrets store: {exc}")
            return {}

    def _persist(self):
        payload = json.dumps(self._secrets, indent=2).encode("utf-8")
        encrypted = self._cipher.encrypt(payload)
        self._secrets_path.write_bytes(encrypted)
        os.chmod(self._secrets_path, 0o600)

    def get_secret(self, key: str) -> Optional[str]:
        env_key = key.upper()
        if env_key in os.environ:
            return os.environ[env_key]
        return self._secrets.get(key)

    def has_secret(self, key: str) -> bool:
        return self.get_secret(key) is not None

    def set_secret(self, key: str, value: str):
        self._secrets[key] = value
        self._persist()

    def delete_secret(self, key: str):
        if key in self._secrets:
            del self._secrets[key]
            self._persist()

    def rotate_secret(self, key: str, new_value: str):
        self.set_secret(key, new_value)

    def list_secrets(self) -> Dict[str, bool]:
        """
        Returns a masked view of which secrets are configured.
        """
        return {key: True for key in self._secrets.keys()}


secrets_manager = SecretsManager()
