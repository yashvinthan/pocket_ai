from pocket_ai.core.config import get_config
from pocket_ai.core.logger import logger

class TTSEngine:
    def speak(self, text: str):
        logger.info(f"TTS Speaking: {text}")
        # Implement Piper or Coqui here
        pass

tts_engine = TTSEngine()
