#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Restore/enhance images using Gemini with automatic model fallback.
Zero external dependencies — uses only Python stdlib.

Usage:
    python3 restore.py --filename "output.png" -i damaged_photo.png
    python3 restore.py --filename "output.png" -i old_photo.png --prompt "restore colors"
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import generate_with_fallback, get_api_key, load_image_as_base64, save_image

DEFAULT_PROMPT = (
    "Restore this image. Fix any damage, scratches, noise, or degradation. "
    "Enhance clarity and colors while preserving the original composition."
)


def main():
    parser = argparse.ArgumentParser(description="Restore/enhance images with Gemini (auto-fallback)")
    parser.add_argument("--filename", "-f", required=True, help="Output filename")
    parser.add_argument("--input-image", "-i", required=True, dest="input", help="Input image")
    parser.add_argument("--prompt", "-p", default=DEFAULT_PROMPT, help="Custom restore instructions")
    parser.add_argument("--resolution", "-r", choices=["1K", "2K", "4K"], default="1K")
    parser.add_argument("--api-key", "-k", help="Gemini API key (overrides env)")
    args = parser.parse_args()

    api_key = get_api_key(args.api_key)
    output_path = Path(args.filename)

    data, mime = load_image_as_base64(args.input)
    print(f"Loaded: {args.input}")

    print(f"Restoring image ({args.resolution})...")
    result, model_used = generate_with_fallback(
        api_key, args.prompt, args.resolution, input_images_b64=[(data, mime)],
    )
    save_image(result, output_path, model_used)


if __name__ == "__main__":
    main()
