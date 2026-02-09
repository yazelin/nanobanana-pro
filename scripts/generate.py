#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "google-genai>=1.0.0",
#     "pillow>=10.0.0",
# ]
# ///
"""
Generate images using Gemini with automatic model fallback.

Usage:
    uv run generate.py --prompt "description" --filename "output.png" [--resolution 1K|2K|4K]
"""

import argparse
import sys
from pathlib import Path

# Add script dir to path for _common import
sys.path.insert(0, str(Path(__file__).parent))
from _common import generate_with_fallback, get_api_key, save_image


def main():
    parser = argparse.ArgumentParser(description="Generate images with Gemini (auto-fallback)")
    parser.add_argument("--prompt", "-p", required=True, help="Image description")
    parser.add_argument("--filename", "-f", required=True, help="Output filename")
    parser.add_argument("--resolution", "-r", choices=["1K", "2K", "4K"], default="1K")
    parser.add_argument("--api-key", "-k", help="Gemini API key (overrides env)")
    args = parser.parse_args()

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=get_api_key(args.api_key))
    output_path = Path(args.filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Generating image ({args.resolution})...")
    response, model_used = generate_with_fallback(
        client, types, args.prompt, resolution=args.resolution,
    )
    save_image(response, output_path, model_used)


if __name__ == "__main__":
    main()
