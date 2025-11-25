from pocket_ai.wellness.database import wellness_db
from pocket_ai.core.logger import logger
import random

class ActivityTracker:
    def __init__(self):
        self.steps = 0
        self.activity_type = "still"

    def update_from_imu(self, accel_data):
        # Mock logic: if accel > threshold, step++
        # In real life, use a pedometer algorithm
        magnitude = sum([x**2 for x in accel_data]) ** 0.5
        if magnitude > 1.2: # 1G + movement
            self.steps += 1
            self.activity_type = "walking"
        else:
            self.activity_type = "still"

    def log_summary(self):
        logger.info(f"Logging activity: {self.steps} steps")
        # Save to DB (need to add table for activity in real impl)
        pass

activity_tracker = ActivityTracker()
