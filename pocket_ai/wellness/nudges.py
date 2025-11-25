from pocket_ai.core.logger import logger

class NudgeSystem:
    def check_nudges(self):
        # Logic: if time > 1pm and no lunch logged -> nudge
        logger.info("Checking nudges...")
        return ["Time to drink water"]

nudge_system = NudgeSystem()
