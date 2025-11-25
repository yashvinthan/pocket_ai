from typing import List, Dict, Any
import time

class ContextManager:
    def __init__(self, max_turns: int = 10):
        self.history: List[Dict[str, Any]] = []
        self.max_turns = max_turns

    def add_turn(self, user_input: str, agent_response: str, intent: Dict[str, Any]):
        turn = {
            "timestamp": time.time(),
            "user": user_input,
            "agent": agent_response,
            "intent": intent
        }
        self.history.append(turn)
        if len(self.history) > self.max_turns:
            self.history.pop(0)

    def get_context(self) -> List[Dict[str, Any]]:
        return self.history

    def get_last_intent(self) -> Dict[str, Any]:
        if not self.history:
            return {}
        return self.history[-1].get("intent", {})

context_manager = ContextManager()
