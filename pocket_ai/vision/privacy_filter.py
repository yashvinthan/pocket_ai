from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np  # type: ignore[import]
from PIL import Image, ImageFilter  # type: ignore[import]

try:
    import cv2  # type: ignore[import]
except ImportError:
    cv2 = None  # type: ignore[assignment]

from pocket_ai.core.logger import logger


@dataclass
class PrivacyFilterConfig:
    blur_radius: int = 12
    redact_faces: bool = True
    strip_metadata: bool = True


class PrivacyFilter:
    def __init__(self, config: Optional[PrivacyFilterConfig] = None):
        self.config = config or PrivacyFilterConfig()
        self._face_cascade = self._load_face_cascade() if self.config.redact_faces else None

    def process_image(self, image_bytes: bytes) -> bytes:
        """
        Removes EXIF metadata and blurs detected faces.
        """
        if not image_bytes:
            raise ValueError("No image payload provided to privacy filter.")

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        if self.config.redact_faces:
            self._apply_face_blur(image)

        if self.config.strip_metadata:
            image.info.pop("exif", None)

        buffer = io.BytesIO()
        save_kwargs = {"format": "JPEG", "quality": 95}
        image.save(buffer, **save_kwargs)
        buffer.seek(0)
        return buffer.read()

    def _apply_face_blur(self, image: Image.Image) -> None:
        if not self._face_cascade:
            logger.debug("Face cascade unavailable; skipping facial redaction.")
            return

        array = np.array(image)
        gray = cv2.cvtColor(array, cv2.COLOR_RGB2GRAY)
        faces = self._face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

        if len(faces) == 0:
            return

        for (x, y, w, h) in faces:
            region = image.crop((x, y, x + w, y + h))
            blurred = region.filter(ImageFilter.GaussianBlur(radius=self.config.blur_radius))
            image.paste(blurred, (x, y))

        logger.debug("Blurred %s faces for privacy.", len(faces))

    @staticmethod
    def _load_face_cascade():
        if not cv2:
            return None
        cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        if not cascade_path.exists():
            logger.warning("OpenCV cascade not found at %s", cascade_path)
            return None
        classifier = cv2.CascadeClassifier(str(cascade_path))
        if classifier.empty():
            logger.warning("Failed to load face cascade from %s", cascade_path)
            return None
        return classifier


privacy_filter = PrivacyFilter()
