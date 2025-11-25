from __future__ import annotations

from pocket_ai.core.logger import logger

try:
    import audioop
except ImportError:  # pragma: no cover - optional dep on Windows
    audioop = None
    logger.warning("audioop module unavailable; skipping offline noise suppression.")


class SimpleNoiseSuppressor:
    """
    Lightweight noise gate that operates on PCM16 audio frames.
    """

    def __init__(self, threshold: int = 500):
        self.threshold = threshold

    def denoise(self, frame: bytes) -> bytes:
        if not audioop:
            return frame
        rms = audioop.rms(frame, 2)
        if rms < self.threshold:
            # Zero out low-energy frames
            return b"\x00" * len(frame)
        return frame


noise_suppressor = SimpleNoiseSuppressor()
