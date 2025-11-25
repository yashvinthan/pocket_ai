# POCKET-AI Architecture

## Overview
POCKET-AI is a modular, offline-first AI assistant designed for Raspberry Pi 5.

## Modules

### Core (`/core`)
- **Config**: Central configuration and routing matrix.
- **Policy Engine**: Enforces privacy profiles (OFFLINE_ONLY, HYBRID).
- **Compute Backends**: Selects execution path (CPU, TPU, GPU Server).
- **Storage**: Encrypted local storage with TTL.

### AI (`/ai`)
- **Orchestrator**: Central brain, routes inputs to NLU, Tools, or LLM.
- **Local LLM**: Wrapper for Phi-2/Llama via GGUF.
- **OpenAI Gateway**: Optional cloud layer, strictly policy-controlled.

### Vision (`/vision`)
- **Offline**: MobileNet V2 (CPU) or Edge TPU models.
- **Online**: GPT-4 Vision (optional).

### Audio (`/audio`)
- **Wake Word**: Porcupine / Precise.
- **STT**: Vosk (Command) + Whisper (Dictation).
- **TTS**: Piper (High quality offline).

### Tools (`/tools`)
- **Easy Mode**: YAML-defined workflows.
- **Dev Mode**: Python plugins with capability security.

### MCP (`/mcp`)
- Exposes assistant capabilities to external clients via Model Context Protocol.
