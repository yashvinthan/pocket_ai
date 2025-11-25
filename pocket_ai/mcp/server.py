from __future__ import annotations

import json
from typing import Any, Dict

from pocket_ai.ai.orchestrator import orchestrator
from pocket_ai.core.config import get_config
from pocket_ai.core.internet_checker import internet_checker
from pocket_ai.core.logger import logger
from pocket_ai.core.security import verify_token
from pocket_ai.core.storage import storage
from pocket_ai.tools.easy_tools_runtime import easy_tools
from pocket_ai.tools.tool_registry import tool_registry


class MCPServer:
    def __init__(self):
        self.tools = []
        self._register_tools()

    def _register_tools(self):
        self.tools = [
            {
                "name": "assistant_query",
                "description": "Ask the AI assistant a question or give a command.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "run_easy_tool",
                "description": "Execute an Easy Mode tool.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "tool_name": {"type": "string"},
                        "payload": {"type": "object"},
                    },
                    "required": ["tool_name"],
                },
            },
            {
                "name": "run_dev_tool",
                "description": "Execute a developer plugin safely.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "plugin": {"type": "string"},
                        "payload": {"type": "object"},
                    },
                    "required": ["plugin", "payload"],
                },
            },
            {
                "name": "assistant_status",
                "description": "Get current profile, connectivity, and integrations.",
                "input_schema": {"type": "object", "properties": {}},
            },
            {
                "name": "assistant_profile_set",
                "description": "Change the active privacy profile.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "profile": {"type": "string", "enum": ["OFFLINE_ONLY", "HYBRID", "CUSTOM"]}
                    },
                    "required": ["profile"],
                },
            },
            {
                "name": "assistant_data_control",
                "description": "Manage user data lifecycle.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["list_categories", "export", "delete", "factory_reset"],
                        },
                        "category": {"type": "string"},
                    },
                    "required": ["operation"],
                },
            },
            {
                "name": "list_tools",
                "description": "List registered tools.",
                "input_schema": {"type": "object", "properties": {}},
            },
        ]

    async def handle_request(self, method: str, params: Dict[str, Any]) -> Any:
        if method != "tools/call" and method != "tools/list":
            raise ValueError(f"Method not supported: {method}")

        if method == "tools/list":
            return {"tools": self.tools}

        tool_name = params.get("name")
        args = params.get("arguments", {})
        self._ensure_authorized(params.get("auth_token"))
        logger.info(f"MCP Call: {tool_name}")

        if tool_name == "assistant_query":
            return await orchestrator.process_text_command(args["query"])

        if tool_name == "run_easy_tool":
            result = await easy_tools.execute_tool(args["tool_name"], args.get("payload", {}))
            return {"content": [{"type": "text", "text": json.dumps(result)}]}

        if tool_name == "run_dev_tool":
            plugin = args["plugin"]
            payload = args.get("payload", {})
            response = await tool_registry.execute_dev_plugin(plugin, payload)
            return {"content": [{"type": "text", "text": json.dumps(response)}]}

        if tool_name == "assistant_status":
            cfg = get_config()
            status = {
                "profile": cfg.profile,
                "internet": internet_checker.is_connected(),
                "routing": cfg.routing.model_dump(),
                "integrations": list(cfg.enabled_integrations),
            }
            return {"content": [{"type": "text", "text": json.dumps(status)}]}

        if tool_name == "assistant_profile_set":
            cfg = get_config()
            cfg.profile = args["profile"]
            return {"content": [{"type": "text", "text": f"Profile switched to {cfg.profile}"}]}

        if tool_name == "assistant_data_control":
            op = args["operation"]
            if op == "list_categories":
                return {"content": [{"type": "text", "text": json.dumps(storage.list_categories(), indent=2)}]}
            if op == "export":
                export_path = storage.export_user_data(args.get("category"))
                return {"content": [{"type": "text", "text": f"Exported to {export_path}"}]}
            if op == "delete":
                category = args.get("category")
                storage.delete_category(category)
                return {"content": [{"type": "text", "text": f"Deleted category {category}"}]}
            if op == "factory_reset":
                storage.factory_reset()
                return {"content": [{"type": "text", "text": "Factory reset completed."}]}

        if tool_name == "list_tools":
            return {"content": [{"type": "text", "text": json.dumps(tool_registry.list_tools())}]}

        raise ValueError(f"Tool not found: {tool_name}")

    @staticmethod
    def _ensure_authorized(provided_token: str | None):
        cfg = get_config()
        if not cfg.mcp.require_auth:
            return
        if not verify_token("mcp_auth_token", provided_token):
            raise PermissionError("Unauthorized MCP client")


mcp_server = MCPServer()
# Mock MCP Server implementation
# In a real deployment, this would use the `mcp` python SDK.

