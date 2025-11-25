import io
import os
import platform
from dataclasses import dataclass
from typing import List

import numpy as np  # type: ignore[import]
from PIL import Image  # type: ignore[import]

from pocket_ai.core.logger import logger

# Try to import TFLite runtime
try:
    import tflite_runtime.interpreter as tflite  # type: ignore[import]
except ImportError:
    try:
        import tensorflow.lite as tflite  # type: ignore[import]
    except ImportError:
        tflite = None
        logger.warning("No TFLite runtime found. Vision will be disabled.")

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
LABEL_FILE = os.path.join(MODELS_DIR, "labels_mobilenet.txt")


@dataclass
class Detection:
    label: str
    confidence: float


class OfflineVision:
    def __init__(self):
        self.interpreter = None
        self.input_details = None
        self.output_details = None
        self.labels: List[str] = self._load_labels()
        self.min_confidence = 0.35
        self._load_model()

    def _load_labels(self) -> List[str]:
        if os.path.exists(LABEL_FILE):
            with open(LABEL_FILE, "r", encoding="utf-8") as handle:
                return [line.strip() for line in handle if line.strip()]
        # Fallback to ImageNet placeholder labels
        return [f"class_{idx}" for idx in range(1001)]

    def _load_model(self):
        if not tflite:
            return

        tpu_model_path = os.path.join(MODELS_DIR, "mobilenet_v2_1.0_224_quant_edgetpu.tflite")
        cpu_model_path = os.path.join(MODELS_DIR, "mobilenet_v2_1.0_224.tflite")

        try:
            self.interpreter = self._try_load_edgetpu(tpu_model_path)
        except Exception as exc:
            logger.debug("TPU delegate unavailable: %s", exc)
            self.interpreter = None

        if not self.interpreter and os.path.exists(cpu_model_path):
            logger.info("Vision: Falling back to CPU model.")
            self.interpreter = tflite.Interpreter(model_path=cpu_model_path)

        if not self.interpreter:
            logger.error("Vision: No compatible models found.")
            return

        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        logger.info("Vision: Offline model ready (input=%s).", self.input_details[0]["shape"])

    def _try_load_edgetpu(self, model_path: str):
        if not os.path.exists(model_path):
            raise FileNotFoundError("TPU model missing.")
        lib_name = "libedgetpu.so.1" if platform.system() == "Linux" else "edgetpu.dll"
        delegate = tflite.load_delegate(lib_name)
        logger.info("Vision: Loaded Edge TPU delegate.")
        return tflite.Interpreter(model_path=model_path, experimental_delegates=[delegate])

    def detect_objects(self, image_bytes: bytes) -> List[Detection]:
        if not self.interpreter or not self.input_details or not self.output_details:
            return []
        if not image_bytes:
            raise ValueError("Empty image payload provided to OfflineVision.")

        tensor = self._preprocess(image_bytes)
        self.interpreter.set_tensor(self.input_details[0]["index"], tensor)
        self.interpreter.invoke()

        output = self.interpreter.get_tensor(self.output_details[0]["index"])
        output = self._dequantize(output, self.output_details[0])
        scores = output.squeeze()

        top_indices = scores.argsort()[-5:][::-1]
        detections: List[Detection] = []
        for idx in top_indices:
            score = float(scores[idx])
            if score < self.min_confidence:
                continue
            label = self.labels[idx] if idx < len(self.labels) else f"class_{idx}"
            detections.append(Detection(label=label, confidence=round(score, 4)))

        return detections

    def _preprocess(self, image_bytes: bytes):
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        input_info = self.input_details[0]
        height, width = input_info["shape"][1:3]
        image = image.resize((width, height))
        array = np.asarray(image)
        array = np.expand_dims(array, axis=0)

        if input_info["dtype"] == np.uint8:
            return array.astype(np.uint8)

        normalized = (array.astype(np.float32) / 127.5) - 1.0
        return normalized

    @staticmethod
    def _dequantize(output, output_info):
        if output_info["dtype"] != np.uint8:
            return output
        scale, zero_point = output_info.get("quantization", (1.0, 0))
        if scale <= 0:
            return output
        return (output.astype(np.float32) - zero_point) * scale


vision_offline = OfflineVision()
