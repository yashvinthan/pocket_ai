from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Set

import yaml
from pydantic import BaseModel, Field

from pocket_ai.core.constants import INTEGRATION_PLUGIN_MAP, ROUTING_DEFAULTS


ROUTING_FIELD_BY_INTENT = {
    "create_task": "task_app",
    "create_note": "notes_app",
    "block_time": "calendar_app",
    "draft_email": "email_app",
    "summarize_chat": "chat_app",
    "order_food": "food_app",
}


class RoutingMatrix(BaseModel):
    task_app: str = Field(default=ROUTING_DEFAULTS["task_app"])
    notes_app: str = Field(default=ROUTING_DEFAULTS["notes_app"])
    calendar_app: str = Field(default=ROUTING_DEFAULTS["calendar_app"])
    email_app: str = Field(default=ROUTING_DEFAULTS["email_app"])
    chat_app: str = Field(default=ROUTING_DEFAULTS["chat_app"])
    food_app: str = Field(default=ROUTING_DEFAULTS["food_app"])

    def to_plugins(self) -> Dict[str, str]:
        """
        Resolve routing entries into plugin identifiers.
        """
        mapping = {}
        for intent_key, attr in ROUTING_FIELD_BY_INTENT.items():
            target = getattr(self, attr)
            plugin = INTEGRATION_PLUGIN_MAP.get(target, "")
            mapping[intent_key] = plugin
        return mapping

    def enabled_targets(self) -> Set[str]:
        values = {
            self.task_app,
            self.notes_app,
            self.calendar_app,
            self.email_app,
            self.chat_app,
            self.food_app,
        }
        return {value for value in values if value not in {"local", "none", ""}}


class ApiSecurity(BaseModel):
    bind_host: str = "127.0.0.1"
    allowed_origins: List[str] = Field(default_factory=lambda: ["http://localhost"])
    require_auth: bool = True


class MCPConfig(BaseModel):
    require_auth: bool = True


class Config(BaseModel):
    profile: str = "OFFLINE_ONLY"
    storage_path: str = "data"
    routing: RoutingMatrix = Field(default_factory=RoutingMatrix)
    feature_flags: Dict[str, bool] = Field(default_factory=dict)
    cloud_overrides: Dict[str, bool] = Field(default_factory=dict)
    api: ApiSecurity = Field(default_factory=ApiSecurity)
    mcp: MCPConfig = Field(default_factory=MCPConfig)

    def __init__(self, **data):
        super().__init__(**data)
        Path(self.storage_path).mkdir(parents=True, exist_ok=True)

    @property
    def enabled_integrations(self) -> Set[str]:
        plugins = {self.plugin_for_intent(intent) for intent in ROUTING_FIELD_BY_INTENT}
        return {plugin for plugin in plugins if plugin}

    def plugin_for_intent(self, intent_type: str) -> str:
        attr = ROUTING_FIELD_BY_INTENT.get(intent_type)
        if not attr:
            return ""
        target = getattr(self.routing, attr, "local")
        return INTEGRATION_PLUGIN_MAP.get(target, "")


_config_instance: Optional["Config"] = None


def _deep_update(base: Dict, incoming: Dict) -> Dict:
    result = dict(base)
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_update(result[key], value)
        else:
            result[key] = value
    return result


def load_config(config_path: str = "config.yaml") -> Config:
    global _config_instance

    config_data: Dict[str, Dict] = {
        "profile": os.environ.get("POCKET_PROFILE", "OFFLINE_ONLY"),
        "storage_path": os.environ.get("POCKET_STORAGE_PATH", "data"),
        "routing": {},
        "feature_flags": {},
        "cloud_overrides": {},
        "api": {},
        "mcp": {},
    }

    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            yaml_config = yaml.safe_load(f) or {}
            config_data = _deep_update(config_data, yaml_config)

    _config_instance = Config(**config_data)
    return _config_instance


def get_config() -> Config:
    global _config_instance
    if _config_instance is None:
        return load_config()
    return _config_instance
