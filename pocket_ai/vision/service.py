from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from pocket_ai.core.logger import logger
from pocket_ai.vision.camera import Camera, CameraError, camera
from pocket_ai.vision.privacy_filter import privacy_filter
from pocket_ai.vision.trigger import vision_trigger

try:
    from pocket_ai.vision.vision_offline import Detection, vision_offline
except ImportError:  # pragma: no cover - optional component
    vision_offline = None  # type: ignore[assignment]
    Detection = None  # type: ignore[assignment]

from pocket_ai.vision.vision_online import vision_online


@dataclass
class VisionResult:
    status: str
    reason: str
    frame_bytes: Optional[bytes] = None
    frame_metadata: Optional[Dict[str, Any]] = None
    offline_detections: Optional[List[Dict[str, Any]]] = None
    online_summary: Optional[str] = None


class VisionService:
    """
    High-level orchestrator for the capture -> sanitize -> inference flow.
    """

    def __init__(self, camera_driver: Camera = camera):
        self.camera = camera_driver
        self.trigger = vision_trigger
        self.privacy = privacy_filter
        self.offline = vision_offline
        self.online = vision_online

    async def capture_and_process(
        self,
        *,
        user_requested: bool,
        prompt: Optional[str] = None,
        use_online: bool = False,
    ) -> VisionResult:
        decision = self.trigger.should_capture(user_requested=user_requested)
        if not decision.allowed:
            return VisionResult(status="blocked", reason=decision.reason)

        try:
            frame = self.camera.capture_frame()
        except CameraError as exc:
            logger.error("Camera capture failed: %s", exc)
            return VisionResult(status="error", reason="capture_failed")

        filtered_bytes = self.privacy.process_image(frame.data)
        offline_results = self._run_offline(filtered_bytes)

        online_summary = None
        if use_online and prompt:
            online_summary = await self._run_online(filtered_bytes, prompt)

        return VisionResult(
            status="ok",
            reason="captured",
            frame_bytes=filtered_bytes,
            frame_metadata={"width": frame.width, "height": frame.height, "timestamp": frame.timestamp},
            offline_detections=offline_results,
            online_summary=online_summary,
        )

    def _run_offline(self, image_bytes: bytes) -> Optional[List[Dict[str, Any]]]:
        if not self.offline:
            logger.debug("Offline vision unavailable.")
            return None
        detections = self.offline.detect_objects(image_bytes)
        if not detections:
            return []
        if Detection and detections and isinstance(detections[0], Detection):
            return [asdict(item) for item in detections]
        return [
            item if isinstance(item, dict) else {"label": str(item), "confidence": None}
            for item in detections
        ]

    async def _run_online(self, image_bytes: bytes, prompt: str) -> Optional[str]:
        try:
            return await self.online.analyze(image_bytes, prompt)
        except Exception as exc:  # pragma: no cover - network failure path
            logger.error("Online vision request failed: %s", exc)
            return None


vision_service = VisionService()

