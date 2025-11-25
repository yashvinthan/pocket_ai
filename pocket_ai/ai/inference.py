from typing import Any, Optional
from pocket_ai.core.logger import logger
from pocket_ai.ai.local_llm import local_llm
try:
    from pocket_ai.vision.vision_offline import vision_offline
except ImportError:
    vision_offline = None

class LocalInference:
    def __init__(self):
        self.models = {}

    def load_model(self, model_name: str, model_path: str):
        logger.info(f"Loading local model: {model_name}")
        # In a real scenario, we might pre-load models here.
        # For now, LocalLLM and VisionOffline handle their own lazy loading.
        self.models[model_name] = "ready"

    def run_inference(self, model_name: str, input_data: Any) -> Any:
        logger.debug(f"Running inference on {model_name}")
        
        if model_name == "llm":
            # input_data expected to be prompt string
            return local_llm.generate(str(input_data))
            
        if model_name == "vision_classifier":
            if not vision_offline:
                logger.error("Vision offline module not available")
                return None
            # input_data expected to be image path or array
            return vision_offline.detect_objects(input_data)
            
        logger.error(f"Unknown model: {model_name}")
        return None

local_inference = LocalInference()
