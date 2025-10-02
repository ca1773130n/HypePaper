#!/usr/bin/env python3
"""
Download script for quantized LLM model for topic matching.

Downloads a small, quantized 7B parameter model suitable for semantic matching tasks.
Model is stored in backend/models/ directory.
"""

import os
import sys
from pathlib import Path
from urllib.request import urlretrieve


def download_model() -> None:
    """Download quantized LLM model for topic matching."""

    # Create models directory
    models_dir = Path(__file__).parent.parent / "models"
    models_dir.mkdir(exist_ok=True)

    # Model URL - using Mistral 7B Q4_K_M quantized model
    # This is a placeholder URL - replace with actual model download link
    model_url = "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf"
    model_filename = "mistral-7b-instruct-q4_k_m.gguf"
    model_path = models_dir / model_filename

    if model_path.exists():
        print(f"Model already exists at {model_path}")
        print(f"Size: {model_path.stat().st_size / (1024**3):.2f} GB")
        return

    print(f"Downloading model to {model_path}")
    print("This may take a while (model is ~4GB)...")
    print()
    print("NOTE: This is a placeholder script.")
    print("To download the actual model:")
    print(f"1. Visit: {model_url}")
    print(f"2. Download to: {model_path}")
    print()
    print("Alternatively, use huggingface-cli:")
    print(f"  huggingface-cli download TheBloke/Mistral-7B-Instruct-v0.1-GGUF mistral-7b-instruct-v0.1.Q4_K_M.gguf --local-dir {models_dir}")

    # For actual download (commented out to avoid long download during setup):
    # def report_progress(block_num: int, block_size: int, total_size: int) -> None:
    #     downloaded = block_num * block_size
    #     percent = min(downloaded / total_size * 100, 100)
    #     print(f"\rProgress: {percent:.1f}%", end="")

    # try:
    #     urlretrieve(model_url, model_path, reporthook=report_progress)
    #     print(f"\nModel downloaded successfully to {model_path}")
    #     print(f"Size: {model_path.stat().st_size / (1024**3):.2f} GB")
    # except Exception as e:
    #     print(f"\nError downloading model: {e}", file=sys.stderr)
    #     sys.exit(1)


if __name__ == "__main__":
    download_model()
