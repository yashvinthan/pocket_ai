from __future__ import annotations

import json
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet

from pocket_ai.core.config import get_config
from pocket_ai.core.constants import DATA_CATEGORIES
from pocket_ai.core.logger import logger
from pocket_ai.core.policy_engine import policy_engine


class DataLifecycleManager:
    def __init__(self):
        self.config = get_config()
        self.base_path = Path(self.config.storage_path)
        self.system_path = self.base_path / "system"
        self.system_path.mkdir(parents=True, exist_ok=True)
        self._key_path = self.system_path / "storage_master.key"
        self._cipher = Fernet(self._load_or_create_key())

        self.memory_categories = {
            name for name, cfg in DATA_CATEGORIES.items() if cfg["storage"] == "memory"
        }
        self.disk_categories = {
            name for name, cfg in DATA_CATEGORIES.items() if cfg["storage"] == "disk"
        }
        self._memory_cache: Dict[str, Dict[str, Dict[str, Any]]] = {
            cat: {} for cat in self.memory_categories
        }
        self._ensure_directories()

    def _load_or_create_key(self) -> bytes:
        if self._key_path.exists():
            return self._key_path.read_bytes()
        key = Fernet.generate_key()
        self._key_path.write_bytes(key)
        os.chmod(self._key_path, 0o600)
        return key

    def _ensure_directories(self):
        for category in self.disk_categories:
            (self.base_path / category).mkdir(parents=True, exist_ok=True)
        (self.base_path / "exports").mkdir(parents=True, exist_ok=True)

    def _category_schema(self, category: str) -> Dict[str, Any]:
        schema = DATA_CATEGORIES.get(category)
        if not schema:
            raise ValueError(f"Unknown data category: {category}")
        return schema

    def store(self, category: str, key: str, data: Any):
        schema = self._category_schema(category)
        payload = self._serialise(data)
        size_kb = len(payload) / 1024

        if schema["storage"] == "memory":
            self._memory_cache[category][key] = {
                "payload": payload,
                "ts": time.time(),
            }
            return

        if not policy_engine.can_persist(category, size_kb):
            logger.warning(f"Persistence denied for {category}/{key}")
            return

        cipher_text = self._cipher.encrypt(payload) if schema.get("encrypted") else payload
        target_path = self.base_path / category / f"{key}.bin"
        target_path.write_bytes(cipher_text)
        os.chmod(target_path, 0o600)
        logger.debug(f"Stored {category}/{key}")

    def retrieve(self, category: str, key: str) -> Optional[Any]:
        schema = DATA_CATEGORIES.get(category)
        if not schema:
            return None
        if schema["storage"] == "memory":
            record = self._memory_cache[category].get(key)
            if not record:
                return None
            return self._deserialise(record["payload"])

        path = self.base_path / category / f"{key}.bin"
        if not path.exists():
            return None

        data = path.read_bytes()
        if schema.get("encrypted"):
            data = self._cipher.decrypt(data)
        return self._deserialise(data)

    def purge_expired(self):
        now = time.time()
        for category, schema in DATA_CATEGORIES.items():
            ttl = schema["ttl_seconds"]
            if ttl == 0:
                continue

            if schema["storage"] == "memory":
                cache = self._memory_cache[category]
                for key in list(cache.keys()):
                    if now - cache[key]["ts"] > ttl:
                        del cache[key]
                continue

            cat_path = self.base_path / category
            if not cat_path.exists():
                continue
            for file in cat_path.iterdir():
                if file.is_file() and now - file.stat().st_mtime > ttl:
                    file.unlink(missing_ok=True)
                    logger.info(f"Purged expired file: {file}")

    def export_user_data(self, category: Optional[str] = None, destination: Optional[str] = None) -> str:
        categories = [category] if category else list(self.disk_categories)
        export_payload: Dict[str, Dict[str, Any]] = {}
        for cat in categories:
            export_payload[cat] = self._dump_category(cat)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        export_key = destination or f"export_{timestamp}"
        self.store("user_exports", export_key, export_payload)
        logger.info(f"Exported data bundle to encrypted entry {export_key}")
        return export_key

    def list_categories(self) -> Dict[str, Dict[str, Any]]:
        summary = {}
        for cat, schema in DATA_CATEGORIES.items():
            if schema["storage"] == "memory":
                count = len(self._memory_cache[cat])
            else:
                cat_path = self.base_path / cat
                count = len(list(cat_path.glob("*.bin"))) if cat_path.exists() else 0
            summary[cat] = {
                "description": schema["description"],
                "storage": schema["storage"],
                "items": count,
                "ttl_seconds": schema["ttl_seconds"],
            }
        return summary

    def list_keys(self, category: str):
        schema = self._category_schema(category)
        if schema["storage"] == "memory":
            return list(self._memory_cache[category].keys())
        cat_path = self.base_path / category
        if not cat_path.exists():
            return []
        return [file.stem for file in cat_path.glob("*.bin")]

    def delete_record(self, category: str, key: str):
        schema = self._category_schema(category)
        if schema["storage"] == "memory":
            self._memory_cache[category].pop(key, None)
            return
        target_path = self.base_path / category / f"{key}.bin"
        target_path.unlink(missing_ok=True)

    def delete_category(self, category: str):
        schema = self._category_schema(category)
        if schema["storage"] == "memory":
            self._memory_cache[category].clear()
        else:
            cat_path = self.base_path / category
            if cat_path.exists():
                for file in cat_path.glob("*.bin"):
                    file.unlink(missing_ok=True)

    def factory_reset(self):
        logger.warning("FACTORY RESET REQUESTED")
        if self.base_path.exists():
            shutil.rmtree(self.base_path)
        self.__init__()
        logger.warning("Factory reset complete")

    def _dump_category(self, category: str) -> Dict[str, Any]:
        schema = self._category_schema(category)
        payload = {}
        if schema["storage"] == "memory":
            for key, record in self._memory_cache[category].items():
                payload[key] = self._deserialise(record["payload"])
            return payload

        cat_path = self.base_path / category
        if not cat_path.exists():
            return payload

        for file in cat_path.glob("*.bin"):
            data = file.read_bytes()
            if schema.get("encrypted"):
                data = self._cipher.decrypt(data)
            payload[file.stem] = self._deserialise(data)
        return payload

    @staticmethod
    def _serialise(data: Any) -> bytes:
        if isinstance(data, (dict, list)):
            return json.dumps(data, ensure_ascii=False).encode("utf-8")
        if isinstance(data, str):
            return data.encode("utf-8")
        if isinstance(data, bytes):
            return data
        return str(data).encode("utf-8")

    @staticmethod
    def _deserialise(raw: bytes) -> Any:
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            try:
                return raw.decode("utf-8")
            except Exception:
                return raw


storage = DataLifecycleManager()
