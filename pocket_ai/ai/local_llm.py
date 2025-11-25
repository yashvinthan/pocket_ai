from typing import Optional
from pocket_ai.core.logger import logger
from pocket_ai.core.compute_backends import compute_backends, BackendType

class LocalLLM:
    def __init__(self):
        self.model_loaded = False
        # In a real implementation, we would load llama_cpp here
        # self.llm = Llama(model_path="models/phi-2.gguf")

    def generate(self, prompt: str) -> str:
        backend = compute_backends.get_backend_for_task("llm")
        logger.info(f"Local LLM generating response using {backend.value}...")
        
        if backend == BackendType.GPU_SERVER:
            # Call remote GPU server
            return f"Remote GPU Response to: {prompt[:20]}..."
            
        # Default CPU/TPU (TPU doesn't run LLMs usually, so CPU)
        return f"Local Phi-2 Response to: {prompt[:20]}..."

    def is_available(self) -> bool:
        return True

local_llm = LocalLLM()
