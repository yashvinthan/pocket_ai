from __future__ import annotations
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np  # type: ignore[import]

try:
    import cv2  # type: ignore[import]
except ImportError:
    cv2 = None  # type: ignore[assignment]

from pocket_ai.core.logger import logger


class CameraError(RuntimeError):
    """Raised when the camera cannot complete an operation safely."""


@dataclass(slots=True)
class CameraFrame:
    data: bytes
    width: int
    height: int
    timestamp: float = field(default_factory=lambda: time.time())
    format: str = "jpeg"


@dataclass(slots=True)
class CameraConfig:
    device_index: int = 0
    width: int = 640
    height: int = 480
    fps: int = 30
    jpeg_quality: int = 90
    warmup_frames: int = 5
    require_shutter_open: bool = True
    fallback_image: Optional[Path] = None

    def __post_init__(self):
        if self.jpeg_quality < 1 or self.jpeg_quality > 100:
            raise ValueError("jpeg_quality must be between 1-100")


class Camera:
    """
    Thin wrapper around OpenCV capture with optional fallback to a reference
    image. Designed for synchronous single-shot capture triggered by the
    hardware shutter.
    """

    def __init__(self, config: Optional[CameraConfig] = None):
        self.config = config or CameraConfig()
        self._capture = None
        self._lock = threading.Lock()
        self._shutter_open = not self.config.require_shutter_open
        self._last_frame: Optional[CameraFrame] = None

    def open_shutter(self):
        """Called by the hardware driver when the shutter slider is open."""
        self._shutter_open = True
        logger.debug("Camera shutter opened.")

    def close_shutter(self):
        self._shutter_open = False
        logger.debug("Camera shutter closed; lens feed disabled.")

    def capture_frame(self, *, enforce_shutter: bool = True) -> CameraFrame:
        with self._lock:
            if enforce_shutter and self.config.require_shutter_open and not self._shutter_open:
                raise CameraError("Capture blocked: physical shutter is closed.")

            frame = self._snap_via_driver()
            self._last_frame = frame
            return frame

    def last_frame(self) -> Optional[CameraFrame]:
        return self._last_frame

    def _snap_via_driver(self) -> CameraFrame:
        if cv2:
            return self._snap_with_opencv()
        if self.config.fallback_image:
            return self._snap_from_file(self.config.fallback_image)
        raise CameraError("OpenCV not available and no fallback image configured.")

    def _snap_with_opencv(self) -> CameraFrame:
        capture = self._ensure_capture()
        success, frame = capture.read()
        if not success or frame is None:
            raise CameraError("Failed to read from camera sensor.")

        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), self.config.jpeg_quality] if cv2 else []
        ok, buffer = cv2.imencode(".jpg", frame, encode_params) if cv2 else (False, None)
        if not ok or buffer is None:
            raise CameraError("Failed to encode frame as JPEG.")

        height, width = frame.shape[:2]
        return CameraFrame(buffer.tobytes(), width=width, height=height)

    def _ensure_capture(self):
        if self._capture is not None:
            return self._capture
        if not cv2:
            raise CameraError("OpenCV backend not available.")

        capture = cv2.VideoCapture(self.config.device_index)
        if not capture.isOpened():
            raise CameraError(f"Camera index {self.config.device_index} unavailable.")

        capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
        capture.set(cv2.CAP_PROP_FPS, self.config.fps)

        # Warm-up to stabilise exposure/white balance
        for _ in range(self.config.warmup_frames):
            capture.read()

        self._capture = capture
        logger.info(
            "Camera initialised (index=%s, %sx%s @ %sfps)",
            self.config.device_index,
            self.config.width,
            self.config.height,
            self.config.fps,
        )
        return self._capture

    def _snap_from_file(self, image_path: Path) -> CameraFrame:
        if not image_path.exists():
            raise CameraError(f"Fallback image not found: {image_path}")
        data = image_path.read_bytes()
        # Attempt to read dimensions for metadata; fall back to config.
        width, height = self.config.width, self.config.height
        if cv2:
            array = np.frombuffer(data, dtype=np.uint8)
            image = cv2.imdecode(array, cv2.IMREAD_COLOR)
            if image is not None:
                height, width = image.shape[:2]
        return CameraFrame(data=data, width=width, height=height)

    def release(self):
        with self._lock:
            if self._capture:
                self._capture.release()
                self._capture = None
                logger.info("Camera released.")


camera = Camera()
