from typing import Dict, Any
from .plugin_base import PluginBase, ToolContext
from pocket_ai.core.logger import logger

class TodoistPlugin(PluginBase):
    name = "todoist_tasks"
    description = "Manage tasks in Todoist"
    requires_capabilities = ["network", "secrets:todoist_token"]

    async def execute(self, input_data: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        action = input_data.get("action", "create")
        content = input_data.get("content", "")
        
        logger.info(f"Todoist Plugin executing: {action} - {content}")
        
        # Mock implementation
        if action == "create":
            return {
                "status": "success",
                "task_id": "mock_123",
                "content": content,
                "app": "Todoist"
            }

        if action == "list_open_tasks":
            return {
                "status": "success",
                "tasks": [
                    {"content": "Finalize budget", "due": "tomorrow"},
                    {"content": "Email Arjun", "due": "Friday"},
                ],
            }
        
        return {"status": "error", "message": "Unknown action"}
