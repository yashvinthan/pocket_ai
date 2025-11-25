from enum import Enum
from typing import Optional
from pocket_ai.core.config import get_config
from pocket_ai.core.logger import logger

class BackendType(Enum):
    PI_CPU = "PI_CPU"
    PI_TPU = "PI_TPU"
    GPU_SERVER = "GPU_SERVER"

class ComputeBackends:
    def __init__(self):
        self.config = get_config()
        self.tpu_available = False
        self.gpu_server_available = False
        self._detect_hardware()

    def _detect_hardware(self):
        # 1. Detect TPU
        try:
            # Simple check: look for the library or device
            # Real impl would check usb devices or try loading delegate
            import platform
            lib_name = 'libedgetpu.so.1' if platform.system() == 'Linux' else 'edgetpu.dll'
            # We assume if we can't load it, it's not there. 
            # For prototype, we'll just check a flag or mock it.
            # self.tpu_available = True 
            pass
        except:
            pass
            
        # 2. Detect GPU Server
        # Check config for GPU server URL and ping it
        if self.config.feature_flags.get("gpu_server_url"):
            self.gpu_server_available = True # Mock check

    def get_backend_for_task(self, task_type: str) -> BackendType:
        """
        Decide which backend to use for a task (vision, stt, llm).
        """
        # 1. Check Profile (OFFLINE_ONLY blocks GPU_SERVER unless trusted)
        profile = self.config.profile
        allow_remote = (profile != "OFFLINE_ONLY")
        
        # 2. Task Specific Logic
        if task_type == "vision":
            if self.tpu_available:
                return BackendType.PI_TPU
            if allow_remote and self.gpu_server_available:
                return BackendType.GPU_SERVER
            return BackendType.PI_CPU
            
        elif task_type == "llm":
            if allow_remote and self.gpu_server_available:
                return BackendType.GPU_SERVER
            return BackendType.PI_CPU
            
        return BackendType.PI_CPU

compute_backends = ComputeBackends()
