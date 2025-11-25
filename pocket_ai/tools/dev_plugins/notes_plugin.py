from typing import Any, Dict
import re
import time

from pocket_ai.core.logger import logger
from pocket_ai.core.storage import storage

from .plugin_base import PluginBase, ToolContext


SAFE_KEY = re.compile(r"^[A-Za-z0-9_\-\.]+$")


class NotesPlugin(PluginBase):
    name = "notes"
    description = "Manage simple text notes offline"
    requires_capabilities = ["storage:user_notes"]

    async def execute(self, input_data: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        action = input_data.get("action", "list").lower()
        filename = input_data.get("filename")
        content = input_data.get("content", "")

        if action == "list":
            return {"status": "success", "notes": storage.list_keys("user_notes")}

        if action == "capture_note":
            filename = filename or f"note_{int(time.time())}.txt"

        if not filename or not SAFE_KEY.match(filename):
            return {"status": "error", "message": "Invalid or missing filename"}

        if action == "write":
            storage.store("user_notes", filename, {"content": content, "updated_at": time.time()})
            return {"status": "success", "message": f"Note {filename} saved"}

        if action == "append":
            existing = storage.retrieve("user_notes", filename) or {}
            merged_content = (existing.get("content") or "").rstrip()
            merged_content = f"{merged_content}\n{content}" if merged_content else content
            storage.store("user_notes", filename, {"content": merged_content, "updated_at": time.time()})
            return {"status": "success", "message": f"Appended to {filename}"}

        if action == "read":
            data = storage.retrieve("user_notes", filename)
            if not data:
                return {"status": "error", "message": "Note not found"}
            return {"status": "success", "filename": filename, "content": data.get("content", "")}

        if action == "delete":
            storage.delete_record("user_notes", filename)
            return {"status": "success", "message": f"Deleted {filename}"}

        logger.warning("Notes plugin received unsupported action: %s", action)
        return {"status": "error", "message": "Unknown action"}
