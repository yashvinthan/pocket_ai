from __future__ import annotations

from typing import Any, Dict

from pocket_ai.core.logger import logger

from .plugin_base import PluginBase, ToolContext


class SlackBridgePlugin(PluginBase):
    name = "slack_bridge"
    description = "Summarize unread Slack threads and draft replies"
    requires_capabilities = ["network", "secrets:slack_token"]

    async def execute(self, input_data: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        action = input_data.get("action")

        if action == "summarize_unread":
            channel = input_data.get("channel", "#general")
            logger.info(f"Slack: summarizing unread messages in {channel}")
            return {
                "status": "success",
                "summary": f"Unread messages in {channel}: 2 threads requiring attention.",
            }

        if action == "draft_reply":
            thread_id = input_data.get("thread_id", "latest")
            logger.info(f"Slack: drafting reply for thread {thread_id}")
            return {
                "status": "success",
                "draft": "Here's a quick status update. Let me know if you need more detail.",
            }

        return {"status": "error", "message": "Unsupported action"}


