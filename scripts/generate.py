#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Generate images using Gemini with automatic model fallback.
Zero external dependencies — uses only Python stdlib.

Usage:
    python3 generate.py --prompt "description" --filename "output.png" [--resolution 1K|2K|4K]
    uv run generate.py --prompt "description" --filename "output.png"
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import generate_with_fallback, get_api_key, save_image


def main():
    parser = argparse.ArgumentParser(description="Generate images with Gemini (auto-fallback)")
    parser.add_argument("--prompt", "-p", required=True, help="Image description")
    parser.add_argument("--filename", "-f", required=True, help="Output filename")
    parser.add_argument("--resolution", "-r", choices=["1K", "2K", "4K"], default="1K")
    parser.add_argument("--api-key", "-k", help="Gemini API key (overrides env)")
    args = parser.parse_args()

    api_key = get_api_key(args.api_key)
    output_path = Path(args.filename)

    print(f"Generating image ({args.resolution})...")
    result, model_used = generate_with_fallback(api_key, args.prompt, args.resolution)
    save_image(result, output_path, model_used)


if __name__ == "__main__":
    main()
