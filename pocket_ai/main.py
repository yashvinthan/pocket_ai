import os

import uvicorn

from pocket_ai.core.config import get_config
from pocket_ai.core.logger import logger
from pocket_ai.core.onboarding import run_first_boot_setup
from pocket_ai.tools.dev_tools_loader import load_plugins
from pocket_ai.ui.api import app

def main():
    logger.info("Starting POCKET-AI...")
    run_first_boot_setup()

    # 1. Load Plugins
    load_plugins()

    # 2. Start UI Server (FastAPI)
    cfg = get_config()
    port = int(os.environ.get("PORT", os.environ.get("POCKET_PORT", 8000)))
    host = os.environ.get("HOST", cfg.api.bind_host)
    ssl_cert = os.environ.get("POCKET_TLS_CERT")
    ssl_key = os.environ.get("POCKET_TLS_KEY")
    logger.info(f"Starting UI on {host}:{port}")
    uvicorn.run(
        app,
        host=host,
        port=port,
        ssl_certfile=ssl_cert,
        ssl_keyfile=ssl_key,
    )

if __name__ == "__main__":
    main()
