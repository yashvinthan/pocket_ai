"""
Central constants used across the POCKET-AI runtime.

Keeping these values in a single module avoids circular imports
between config, policy, and the feature modules.
"""

from __future__ import annotations

from typing import Dict, List, Mapping

# Data categories respected by the storage subsystem.
# Each category defines whether it is persisted, its TTL, and if the payload
# must be encrypted on disk. Categories marked as `storage: "memory"`
# are never written to disk and live only inside the process.
DATA_CATEGORIES: Dict[str, Dict[str, object]] = {
    "audio_buffers": {
        "description": "Ephemeral microphone capture used for wake-word + ASR",
        "storage": "memory",
        "ttl_seconds": 5,
        "encrypted": False,
    },
    "image_frames": {
        "description": "Single frames captured when the user explicitly requests vision",
        "storage": "memory",
        "ttl_seconds": 10,
        "encrypted": False,
    },
    "transcripts_temp": {
        "description": "Short lived transcripts (for context + undo)",
        "storage": "disk",
        "ttl_seconds": 300,
        "encrypted": True,
    },
    "wellness_logs": {
        "description": "Structured wellness entries (meals, activity, focus)",
        "storage": "disk",
        "ttl_seconds": 60 * 60 * 24 * 90,  # 90 days by default
        "encrypted": True,
    },
    "routing_config": {
        "description": "User routing matrix + preferences",
        "storage": "disk",
        "ttl_seconds": 0,  # persistent until reset
        "encrypted": True,
    },
    "preferences": {
        "description": "Light-weight UI + device preferences",
        "storage": "disk",
        "ttl_seconds": 0,
        "encrypted": True,
    },
    "tokens": {
        "description": "OAuth tokens / refresh tokens for integrations",
        "storage": "disk",
        "ttl_seconds": 0,
        "encrypted": True,
    },
    "user_notes": {
        "description": "User-authored notes captured via plugins or UI",
        "storage": "disk",
        "ttl_seconds": 0,
        "encrypted": True,
    },
    "user_exports": {
        "description": "Encrypted data export bundles for user download",
        "storage": "disk",
        "ttl_seconds": 60 * 60 * 24,  # 24h retention by default
        "encrypted": True,
    },
}

# Default routing matrix – each intent type maps to an external app.
ROUTING_DEFAULTS: Dict[str, str] = {
    "task_app": "local",
    "notes_app": "local",
    "calendar_app": "local",
    "email_app": "local",
    "chat_app": "local",
    "food_app": "none",
}

# Map routing target -> plugin identifier registered inside tool_registry.
INTEGRATION_PLUGIN_MAP: Mapping[str, str] = {
    "todoist": "todoist_tasks",
    "notion": "notion_integration",
    "google_calendar": "google_calendar",
    "google_tasks": "google_calendar",  # reuse same connector for demo
    "gmail": "gmail_helper",
    "outlook": "gmail_helper",
    "slack": "slack_bridge",
    "teams": "slack_bridge",
    "swiggy": "swiggy_connector",
    "zomato": "zomato_connector",
    "local": "",
    "none": "",
}

# Operations that the policy engine understands for cloud gating.
CLOUD_OPERATION_GROUPS: Mapping[str, List[str]] = {
    "llm": ["chat_completion", "easy_tool", "assistant_query"],
    "vision": ["vision_query"],
    "speech": ["speech_online"],
}

# Capabilities that are never granted automatically.
DENY_BY_DEFAULT_CAPABILITIES = {"shell", "camera_raw"}

