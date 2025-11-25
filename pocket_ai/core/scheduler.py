import asyncio
import time
from typing import List, Callable, Dict
from pocket_ai.core.logger import logger

class Scheduler:
    def __init__(self):
        self.tasks: List[Dict] = []
        self.running = False

    def add_job(self, func: Callable, interval_seconds: int):
        self.tasks.append({
            "func": func,
            "interval": interval_seconds,
            "last_run": 0
        })

    async def start(self):
        self.running = True
        logger.info("Scheduler started")
        while self.running:
            now = time.time()
            for task in self.tasks:
                if now - task["last_run"] > task["interval"]:
                    try:
                        if asyncio.iscoroutinefunction(task["func"]):
                            await task["func"]()
                        else:
                            task["func"]()
                        task["last_run"] = now
                    except Exception as e:
                        logger.error(f"Scheduler job failed: {e}")
            
            await asyncio.sleep(1)

    def stop(self):
        self.running = False

scheduler = Scheduler()
