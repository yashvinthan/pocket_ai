from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from pocket_ai.core.config import get_config
from pocket_ai.core.policy_engine import policy_engine
from pocket_ai.core.secrets_manager import secrets_manager


class ToolContext:
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.config = get_config()
        self.policy = policy_engine
        self.secrets = secrets_manager


class PluginBase(ABC):
    name: str
    description: str
    requires_capabilities: List[str] = []

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any], context: ToolContext) -> Dict[str, Any]:
        ...
