#!/bin/bash
set -e

echo "=== POCKET-AI Installer ==="

# 1. System Dependencies
echo "Installing system dependencies..."
# sudo apt update
# sudo apt install -y python3-venv python3-pip libatlas-base-dev tesseract-ocr

# 2. Python Environment
echo "Setting up Python environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# 3. Install Python Packages
echo "Installing Python packages..."
pip install -r requirements.txt

# 4. Download Models
echo "Downloading AI Models (This may take a while)..."
python3 -m pocket_ai.models.download_models

echo "=== Installation Complete ==="
echo "Run with: python3 -m pocket_ai"
