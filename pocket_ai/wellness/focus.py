from pocket_ai.core.logger import logger

class FocusTracker:
    def __init__(self):
        self.distractions = 0
        self.focus_score = 100

    def register_app_switch(self):
        self.distractions += 1
        self.focus_score = max(0, self.focus_score - 5)
        logger.info(f"Focus dropped to {self.focus_score}")

    def get_status(self):
        if self.focus_score > 80:
            return "Deep Work"
        elif self.focus_score > 50:
            return "Distracted"
        else:
            return "Doomscrolling"

focus_tracker = FocusTracker()
