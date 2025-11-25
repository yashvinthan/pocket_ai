from __future__ import annotations

from pocket_ai.audio.noise_suppression import noise_suppressor
from pocket_ai.core.logger import logger


class OfflineSpeech:
    """
    Thin wrapper that would normally drive Vosk/Whisper-tiny.
    For now we provide a deterministic stub that still logs the audio path.
    """

    def __init__(self):
        self.model_name = "vosk-small-en"

    def transcribe(self, audio_data: bytes) -> str:
        cleaned = noise_suppressor.denoise(audio_data)
        logger.info(f"Offline ASR ({self.model_name}) processing {len(cleaned)} bytes")
        # Real implementation would feed into Vosk recogniser
        return "transcription unavailable (demo)"


speech_offline = OfflineSpeech()
