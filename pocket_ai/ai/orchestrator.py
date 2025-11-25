from __future__ import annotations

import re
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from pocket_ai.ai.context_manager import context_manager
from pocket_ai.ai.local_llm import local_llm
from pocket_ai.ai.nlu import nlu_engine
from pocket_ai.ai.openai_gateway import openai_gateway
from pocket_ai.audio.speech_offline import speech_offline
from pocket_ai.audio.speech_online import speech_online
from pocket_ai.audio.tts_engine import tts_engine
from pocket_ai.core.config import get_config
from pocket_ai.core.logger import logger
from pocket_ai.core.privacy import scrub_text, summarize_for_log
from pocket_ai.core.policy_engine import policy_engine
from pocket_ai.core.storage import storage
from pocket_ai.tools.dev_plugins.plugin_base import ToolContext
from pocket_ai.tools.easy_tools_runtime import easy_tools
from pocket_ai.tools.tool_registry import tool_registry
from pocket_ai.wellness.meals import meal_logger


class AIOrchestrator:
    def __init__(self):
        self.config = get_config()

    async def process_voice_command(self, audio_data: bytes) -> Dict[str, Any]:
        transcript = speech_offline.transcribe(audio_data)
        if not transcript:
            transcript = speech_online.transcribe(audio_data)
        if not transcript:
            return {"status": "error", "message": "Unable to transcribe audio"}
        return await self.process_text_command(transcript)

    async def process_text_command(self, text: str) -> Dict[str, Any]:
        logger.info(f"Processing command: {summarize_for_log(text)}")
        self.config = get_config()  # pick up runtime changes

        storage_key = f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}"
        storage.store("transcripts_temp", storage_key, {"text": scrub_text(text)})

        intent = nlu_engine.parse(text)
        result = await self._execute_intent(intent)
        response_text = result.get("response_text", "Done.")

        context_manager.add_turn(text, response_text, intent)
        tts_engine.speak(response_text)

        return {
            "transcript": text,
            "intent": intent,
            "result": result,
            "response_text": response_text,
        }

    async def _execute_intent(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        intent_type = intent.get("type")

        handlers = {
            "create_task": self._handle_task,
            "create_note": self._handle_note,
            "block_time": self._handle_time_block,
            "draft_email": self._handle_email,
            "order_food": self._handle_food,
            "log_meal": self._handle_meal,
        }

        if handler := handlers.get(intent_type):
            return await handler(intent)

        response_text = await self._llm_fallback(intent.get("raw", ""))
        return {"status": "success", "response_text": response_text}

    async def _handle_task(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        plugin_name = self.config.plugin_for_intent("create_task") or "notes"
        if not plugin_name:
            return {"status": "error", "response_text": "No task integration configured."}

        payload = {"action": "create", "content": intent.get("content")}
        result = await self._call_plugin(plugin_name, payload)
        return self._integration_response(result, f"Task added via {plugin_name}.")

    async def _handle_note(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        plugin_name = self.config.plugin_for_intent("create_note") or "notes"
        payload = {
            "action": "capture_note",
            "title": "Pocket AI Note",
            "content": intent.get("content"),
        }
        result = await self._call_plugin(plugin_name, payload)
        return self._integration_response(result, "Note captured.")

    async def _handle_time_block(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        plugin_name = self.config.plugin_for_intent("block_time")
        if not plugin_name:
            return {"status": "error", "response_text": "No calendar integration configured."}
        start, end = self._parse_time_block(intent.get("raw", "block 2 hours"))
        payload = {
            "action": "block_time",
            "summary": "Focus block",
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        }
        result = await self._call_plugin(plugin_name, payload)
        return self._integration_response(result, "Time blocked.")

    async def _handle_email(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        plugin_name = self.config.plugin_for_intent("draft_email")
        payload = {"action": "draft_from_last"}
        result = await self._call_plugin(plugin_name or "gmail_helper", payload)
        return self._integration_response(result, "Drafted reply.")

    async def _handle_food(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        plugin_name = self.config.plugin_for_intent("order_food")
        if not plugin_name:
            return {"status": "error", "response_text": "No food integration configured."}
        budget = self._extract_budget(intent.get("raw", ""))
        payload = {
            "action": "search_food",
            "query": intent.get("raw", "dinner"),
            "max_price": budget or 400,
        }
        result = await self._call_plugin(plugin_name, payload)
        restaurants = result.get("restaurants", [])
        if not restaurants:
            return {"status": "success", "response_text": "No restaurants found yet.", "results": result}
        top = restaurants[0]
        return {
            "status": "success",
            "response_text": f"Try {top['name']} - {top['item']} ₹{top['price']}",
            "results": result,
        }

    async def _handle_meal(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        summary = meal_logger.log(intent.get("raw", ""))
        storage.store("wellness_logs", f"meal_{int(time.time())}", {"description": intent.get("raw")})
        return {"status": "success", "response_text": summary}

    def _integration_response(self, result: Dict[str, Any], success_text: str) -> Dict[str, Any]:
        if isinstance(result, dict) and result.get("status") == "error":
            return {"status": "error", "response_text": result.get("message", "Integration failed"), "integration_response": result}
        return {"status": "success", "response_text": success_text, "integration_response": result}

    async def _call_plugin(self, plugin_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        tool = tool_registry.get_tool(plugin_name)
        if not tool or tool["type"] != "dev":
            return {"status": "error", "message": f"Plugin {plugin_name} unavailable"}

        try:
            return await tool_registry.execute_dev_plugin(plugin_name, payload, ToolContext())
        except Exception as exc:
            logger.error(f"Plugin {plugin_name} failed: {exc}")
            return {"status": "error", "message": str(exc)}

    async def _llm_fallback(self, text: str) -> str:
        if policy_engine.can_use_cloud("assistant_query"):
            response = await openai_gateway.chat_completion([{"role": "user", "content": text}])
            if response:
                return response
        logger.info("Falling back to local LLM")
        return local_llm.generate(text)

    def _parse_time_block(self, text: str) -> tuple[datetime, datetime]:
        duration_hours = 2
        match = re.search(r"(\d+)\s*hour", text)
        if match:
            duration_hours = max(1, int(match.group(1)))

        start = datetime.now() + timedelta(hours=1)
        end = start + timedelta(hours=duration_hours)
        return start, end

    def _extract_budget(self, text: str) -> Optional[int]:
        match = re.search(r"₹?(\d+)", text)
        return int(match.group(1)) if match else None


orchestrator = AIOrchestrator()
