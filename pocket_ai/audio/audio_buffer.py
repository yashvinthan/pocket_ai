from __future__ import annotations

from collections import deque
from typing import Deque, Tuple


class AudioBuffer:
    """
    In-memory ring buffer for raw audio samples. This never touches disk.
    """

    def __init__(self, max_seconds: float = 5.0, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.max_samples = int(max_seconds * sample_rate)
        self._buffer: Deque[int] = deque(maxlen=self.max_samples)

    def push(self, samples: bytes):
        # Store as ints for quick slicing
        self._buffer.extend(samples)

    def clear(self):
        self._buffer.clear()

    def snapshot(self) -> Tuple[bytes, int]:
        data = bytes(self._buffer)
        return data, len(self._buffer)


audio_buffer = AudioBuffer()


