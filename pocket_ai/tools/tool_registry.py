from __future__ import annotations

from typing import Any, Dict

from pocket_ai.core.logger import logger
from pocket_ai.core.policy_engine import policy_engine
from pocket_ai.tools.dev_plugins.plugin_base import ToolContext


class ToolRegistry:
    def __init__(self):
        self.easy_tools: Dict[str, Dict[str, Any]] = {}
        self.dev_plugins: Dict[str, Any] = {}

    def register_easy_tool(self, name: str, definition: Dict[str, Any]):
        self.easy_tools[name] = definition
        logger.info(f"Registered Easy Tool: {name}")

    def register_dev_plugin(self, name: str, plugin_instance: Any):
        denied: list[str] = []
        for capability in getattr(plugin_instance, "requires_capabilities", []) or []:
            if not policy_engine.can_use_capability(capability, name):
                denied.append(capability)

        if denied:
            logger.warning(
                "Plugin %s registered but capabilities %s currently denied; will enforce at runtime.",
                name,
                ", ".join(denied),
            )

        self.dev_plugins[name] = plugin_instance
        logger.info(f"Registered Dev Plugin: {name}")

    def get_tool(self, name: str) -> Any:
        if name in self.easy_tools:
            return {"type": "easy", "tool": self.easy_tools[name]}
        if name in self.dev_plugins:
            return {"type": "dev", "tool": self.dev_plugins[name]}
        return None

    async def execute_dev_plugin(
        self, name: str, payload: Dict[str, Any], context: ToolContext | None = None
    ):
        plugin = self.dev_plugins.get(name)
        if not plugin:
            raise ValueError(f"Plugin {name} not registered")
        ctx = context or ToolContext()
        self._enforce_capabilities(plugin, ctx)
        return await plugin.execute(payload, ctx)

    @staticmethod
    def _enforce_capabilities(plugin: Any, context: ToolContext):
        required = getattr(plugin, "requires_capabilities", []) or []
        for capability in required:
            if not context.policy.can_use_capability(capability, plugin.name):
                raise PermissionError(
                    f"Capability '{capability}' denied for plugin {plugin.name}"
                )

    def list_tools(self):
        return {
            "easy_tools": list(self.easy_tools.keys()),
            "dev_plugins": list(self.dev_plugins.keys()),
        }


tool_registry = ToolRegistry()
