import sqlite3
import os
from pocket_ai.core.config import get_config

class WellnessDatabase:
    def __init__(self):
        self.config = get_config()
        self.db_path = os.path.join(self.config.storage_path, "wellness.db")
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS meals
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      timestamp TEXT, 
                      description TEXT, 
                      calories INTEGER)''')
        conn.commit()
        conn.close()

    def log_meal(self, description: str, calories: int = 0):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        import datetime
        timestamp = datetime.datetime.now().isoformat()
        c.execute("INSERT INTO meals (timestamp, description, calories) VALUES (?, ?, ?)",
                  (timestamp, description, calories))
        conn.commit()
        conn.close()

wellness_db = WellnessDatabase()
