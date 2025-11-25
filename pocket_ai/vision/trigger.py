from __future__ import annotations

import time
from dataclasses import dataclass

from pocket_ai.core.policy_engine import policy_engine


@dataclass
class TriggerDecision:
    allowed: bool
    reason: str


class VisionTrigger:
    """
    Event-driven gate for the vision stack. Ensures we only capture when the
    user explicitly asks or presses the shutter and that we respect rate limits.
    """

    def __init__(self):
        self.last_capture = 0.0
        self.cooldown = 1.0  # seconds

    def should_capture(self, user_requested: bool, motion_detected: bool = False) -> TriggerDecision:
        now = time.time()
        if not user_requested:
            return TriggerDecision(False, "no_user_intent")

        if now - self.last_capture < self.cooldown:
            return TriggerDecision(False, "cooldown")

        self.last_capture = now

        # Policy check (vision capture is always local, but logging for audit)
        policy_engine.can_use_cloud("vision_capture_local")
        return TriggerDecision(True, "granted")


vision_trigger = VisionTrigger()


