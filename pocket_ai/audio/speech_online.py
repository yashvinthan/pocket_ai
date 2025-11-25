from pocket_ai.core.policy_engine import policy_engine
from pocket_ai.core.logger import logger

class OnlineSpeech:
    def transcribe(self, audio_data: bytes) -> str:
        if not policy_engine.can_use_cloud("speech_online"):
            logger.warning("Online speech blocked")
            return ""
        
        logger.info("Calling Whisper API...")
        return "Mock Whisper Transcription"

speech_online = OnlineSpeech()
