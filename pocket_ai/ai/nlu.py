import re
from typing import Dict, Any, Optional
from pocket_ai.core.logger import logger

class LocalNLU:
    def __init__(self):
        pass

    def parse_intent(self, text: str) -> Dict[str, Any]:
        text = text.lower()
        logger.debug(f"NLU parsing: {text}")

        # 1. Task Creation
        # "Add task to buy milk" / "Remind me to call mom"
        if "task" in text or "todo" in text or "remind me" in text:
            content = re.sub(r"(add|create|make|a)?\s*(task|todo|note)?\s*(to|that)?\s*", "", text).strip()
            return {"type": "create_task", "content": content, "raw": text}

        # 2. Note Taking
        # "Save a note: ideas for project"
        elif "note" in text and "save" in text:
            content = text.split("note", 1)[1].strip(": ").strip()
            return {"type": "create_note", "content": content, "raw": text}

        # 3. Calendar / Time Blocking
        # "Block 2 hours for deep work"
        elif "block" in text and ("hour" in text or "time" in text):
            return {"type": "block_time", "raw": text}

        # 4. Email
        # "Draft email to manager"
        elif "draft" in text and "email" in text:
            return {"type": "draft_email", "raw": text}

        # 5. Food
        # "Order food" / "Find dinner"
        elif "food" in text or "dinner" in text or "lunch" in text or "order" in text:
            return {"type": "order_food", "raw": text}

        # 6. Wellness (Meal)
        # "I ate pizza" / "Log lunch"
        elif "ate" in text or "log meal" in text:
            return {"type": "log_meal", "raw": text}

        return {"type": "unknown", "raw": text}

    def parse(self, text: str) -> Dict[str, Any]:
        return self.parse_intent(text)

nlu_engine = LocalNLU()
