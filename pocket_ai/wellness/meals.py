from pocket_ai.wellness.database import wellness_db
from pocket_ai.core.logger import logger

class MealLogger:
    def log(self, description: str):
        logger.info(f"Logging meal: {description}")
        # In real app, we'd use LLM to estimate calories
        wellness_db.log_meal(description, calories=500) # Mock calories
        return "Meal logged."

meal_logger = MealLogger()
