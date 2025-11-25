from __future__ import annotations

import json
import os
from typing import Any, Dict

import yaml

from pocket_ai.ai.local_llm import local_llm
from pocket_ai.ai.openai_gateway import openai_gateway
from pocket_ai.core.logger import logger
from pocket_ai.core.policy_engine import policy_engine
from pocket_ai.tools.dev_plugins.plugin_base import ToolContext
from pocket_ai.tools.tool_registry import tool_registry


class EasyToolsRuntime:
    def __init__(self):
        self.tools_path = os.path.join(os.path.dirname(__file__), "easy_definitions")
        self.loaded_tools: Dict[str, Dict[str, Any]] = {}
        self._load_tools()

    def _load_tools(self):
        if not os.path.exists(self.tools_path):
            return

        for filename in os.listdir(self.tools_path):
            if filename.endswith((".yaml", ".yml")):
                try:
                    with open(os.path.join(self.tools_path, filename), "r", encoding="utf-8") as f:
                        tool_def = yaml.safe_load(f) or {}
                        if self._validate_tool_def(tool_def):
                            name = tool_def["name"]
                            self.loaded_tools[name] = tool_def
                            tool_registry.register_easy_tool(name, tool_def)
                            logger.info(f"Loaded Easy Tool: {name}")
                except Exception as exc:
                    logger.error(f"Failed to load easy tool {filename}: {exc}")

    @staticmethod
    def _validate_tool_def(tool_def: Dict[str, Any]) -> bool:
        required = ["name", "description", "prompt_template"]
        return all(key in tool_def for key in required)

    async def _collect_data_sources(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        aggregated: Dict[str, Any] = {}
        for source in tool.get("data_sources", []):
            plugin = source.get("plugin")
            alias = source.get("as")
            payload = source.get("payload", {})
            if not plugin or not alias:
                continue
            try:
                result = await tool_registry.execute_dev_plugin(plugin, payload, ToolContext())
                aggregated[alias] = result
            except Exception as exc:
                aggregated[alias] = {"error": str(exc)}
        return aggregated

    async def execute_tool(self, tool_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        tool = self.loaded_tools.get(tool_name)
        if not tool:
            return {"status": "error", "message": f"Tool {tool_name} not found"}

        # Gather contextual data
        context_inputs = dict(inputs)
        context_inputs.update(await self._collect_data_sources(tool))

        prompt = tool["prompt_template"]
        for key, value in context_inputs.items():
            prepared = json.dumps(value, ensure_ascii=False, indent=2) if isinstance(value, (dict, list)) else value
            prompt = prompt.replace(f"{{{{{key}}}}}", str(prepared))

        prefer_cloud = tool.get("uses_cloud", False)
        response_text: str
        if prefer_cloud and policy_engine.can_use_cloud(f"easy_tool:{tool_name}"):
            response_text = await openai_gateway.chat_completion(
                [{"role": "user", "content": prompt}],
                model=tool.get("model", "gpt-4o-mini"),
            ) or local_llm.generate(prompt)
        else:
            response_text = local_llm.generate(prompt)

        return {
            "status": "success",
            "result": response_text,
            "tool_name": tool_name,
        }


easy_tools = EasyToolsRuntime()
