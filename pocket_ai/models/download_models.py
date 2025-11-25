import os
import sys
import requests
import zipfile
import io
from tqdm import tqdm

# Allow running directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pocket_ai.core.logger import logger

MODELS_DIR = os.path.dirname(os.path.abspath(__file__))

# Define the "Pi 5 Model Pack"
MODELS = {
    # 1. Speech-to-Text (Offline)
    "vosk": {
        "type": "zip",
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
        "folder": "vosk-model-small-en-us-0.15"
    },
    "whisper_tiny": {
        "type": "file",
        "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin",
        "filename": "ggml-tiny.en.bin"
    },

    # 2. Text-to-Speech (Offline)
    "piper_model": {
        "type": "file",
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
        "filename": "en_US-lessac-medium.onnx"
    },
    "piper_config": {
        "type": "file",
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json",
        "filename": "en_US-lessac-medium.onnx.json"
    },

    # 3. LLM (Offline "Brain")
    "phi2_gguf": {
        "type": "file",
        "url": "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf",
        "filename": "phi-2.Q4_K_M.gguf"
    },

    # 4. Embeddings (Offline Memory)
    "embedding_model": {
        "type": "file",
        "url": "https://huggingface.co/Xenova/all-MiniLM-L6-v2/resolve/main/onnx/model.onnx",
        "filename": "all-MiniLM-L6-v2.onnx"
    },

    # 5. Vision (Offline)
    "mobilenet_cpu": {
        "type": "file",
        "url": "https://storage.googleapis.com/download.tensorflow.org/models/tflite/mobilenet_v2_1.0_224.tflite",
        "filename": "mobilenet_v2_1.0_224.tflite"
    },
    "mobilenet_tpu": {
        "type": "file",
        "url": "https://storage.googleapis.com/download.tensorflow.org/models/tflite/mobilenet_v2_1.0_224_quant_edgetpu.tflite",
        "filename": "mobilenet_v2_1.0_224_quant_edgetpu.tflite"
    },
    # Note: YOLO-Nano TFLite link is often version specific, using a placeholder/generic link if available or skipping for now if unstable.
    # We will use a known hosted file or skip if not easily direct-linkable without auth.
    # For now, let's stick to MobileNet as the primary vision model to ensure success.

    # 6. OCR
    "tesseract_eng": {
        "type": "file",
        "url": "https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata",
        "filename": "eng.traineddata"
    }
}

def download_file(url: str, desc: str):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024 * 1024 # 1MB chunks
    
    buffer = io.BytesIO()
    with tqdm(total=total_size, unit='iB', unit_scale=True, desc=desc) as t:
        for data in response.iter_content(block_size):
            t.update(len(data))
            buffer.write(data)
    
    return buffer

def download_to_file(url: str, filepath: str, desc: str):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024 * 1024 
    
    with open(filepath, 'wb') as f:
        with tqdm(total=total_size, unit='iB', unit_scale=True, desc=desc) as t:
            for data in response.iter_content(block_size):
                t.update(len(data))
                f.write(data)

def setup_models():
    logger.info(f"Downloading Pi 5 Model Pack to {MODELS_DIR}...")
    
    for name, info in MODELS.items():
        if info["type"] == "zip":
            target_path = os.path.join(MODELS_DIR, info["folder"])
            if os.path.exists(target_path):
                logger.info(f"Model {name} already exists.")
                continue
            
            logger.info(f"Downloading {name}...")
            try:
                zip_buffer = download_file(info["url"], name)
                with zipfile.ZipFile(zip_buffer) as z:
                    z.extractall(MODELS_DIR)
                logger.info(f"Extracted {name}")
            except Exception as e:
                logger.error(f"Failed to download {name}: {e}")
        
        elif info["type"] == "file":
            target_path = os.path.join(MODELS_DIR, info["filename"])
            if os.path.exists(target_path):
                logger.info(f"Model {name} already exists.")
                continue
                
            logger.info(f"Downloading {name}...")
            try:
                download_to_file(info["url"], target_path, name)
                logger.info(f"Saved {name}")
            except Exception as e:
                logger.error(f"Failed to download {name}: {e}")

if __name__ == "__main__":
    setup_models()
