from __future__ import annotations

from typing import Dict, Optional

from pocket_ai.core.config import Config, get_config
from pocket_ai.core.constants import (
    CLOUD_OPERATION_GROUPS,
    DATA_CATEGORIES,
    DENY_BY_DEFAULT_CAPABILITIES,
)
from pocket_ai.core.logger import log_audit, logger
from pocket_ai.core.profiles import ProfileType, get_profile_config
from pocket_ai.core.secrets_manager import secrets_manager


class PolicyEngine:
    """
    Central enforcement point for privacy, storage, and capability rules.
    """

    def __init__(self):
        self.refresh()

    def refresh(self):
        self.config: Config = get_config()
        self.profile = get_profile_config(self.config.profile)

    def _operation_group(self, operation: str) -> str:
        for group, members in CLOUD_OPERATION_GROUPS.items():
            if operation in members:
                return group
        if operation.startswith("easy_tool"):
            return "llm"
        if operation.startswith("assistant_query"):
            return "llm"
        return operation

    def can_use_cloud(self, operation: str, context: Optional[dict] = None) -> bool:
        self.refresh()
        operation_group = self._operation_group(operation)
        override = self.config.cloud_overrides.get(operation) or self.config.cloud_overrides.get(
            operation_group
        )

        if override is not None:
            allowed = bool(override)
            reason = "config_override"
        elif self.profile.name == ProfileType.OFFLINE_ONLY:
            allowed = False
            reason = "profile_offline_only"
        elif self.profile.name == ProfileType.HYBRID:
            allowed = self._hybrid_allows(operation_group)
            reason = "hybrid_profile"
        else:  # CUSTOM profile falls back to overrides, else safest default
            allowed = self._hybrid_allows(operation_group)
            reason = "custom_profile_default"

        log_audit(f"cloud_access:{operation}", allowed, reason, context or {})
        if not allowed:
            logger.debug(f"Cloud access blocked for {operation} ({reason})")
        return allowed

    def _hybrid_allows(self, group: str) -> bool:
        if group == "llm":
            return self.profile.allow_cloud_llm
        if group == "vision":
            return self.profile.allow_cloud_vision
        if group == "speech":
            return self.profile.allow_cloud_speech
        # Unknown group defaults to False unless explicitly whitelisted
        return False

    def can_use_capability(self, capability: str, plugin_name: str) -> bool:
        self.refresh()
        allowed = True
        reason = "granted"

        if capability in DENY_BY_DEFAULT_CAPABILITIES:
            allowed = False
            reason = "denied_by_default"
        elif capability == "network":
            allowed = plugin_name in self.config.enabled_integrations
            reason = "integration_not_routed" if not allowed else "integration_authorized"
        elif capability.startswith("secrets:"):
            secret_name = capability.split(":", 1)[1]
            allowed = secrets_manager.has_secret(secret_name)
            reason = "secret_missing" if not allowed else "secret_present"
        elif capability.startswith("storage:"):
            category = capability.split(":", 1)[1]
            schema = DATA_CATEGORIES.get(category)
            allowed = bool(schema and schema.get("encrypted"))
            reason = "storage_category_invalid" if not allowed else "storage_allowed"
        elif capability == "system_diagnostics":
            allowed = bool(self.config.feature_flags.get("enable_diagnostics"))
            reason = "diagnostics_disabled" if not allowed else "diagnostics_enabled"
        elif capability == "filesystem":
            allowed = True
            reason = "local_only"
        elif capability == "location":
            allowed = True
            reason = "sensor_allowed"

        log_audit(
            f"capability:{capability}",
            allowed,
            reason,
            {"plugin": plugin_name},
        )
        return allowed

    def can_persist(self, category: str, size_kb: int) -> bool:
        schema = DATA_CATEGORIES.get(category)
        if not schema:
            log_audit(
                f"persist:{category}",
                False,
                "unknown_category",
                {"size_kb": size_kb},
            )
            return False

        storage_type = schema["storage"]
        if storage_type == "memory":
            allowed = False
            reason = "memory_only_category"
        else:
            max_size = schema.get("max_kb")
            allowed = not max_size or size_kb <= max_size
            reason = "size_ok" if allowed else "over_size_limit"

        log_audit(
            f"persist:{category}",
            allowed,
            reason,
            {"size_kb": size_kb},
        )
        return allowed


policy_engine = PolicyEngine()
