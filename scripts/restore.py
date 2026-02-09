#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "google-genai>=1.0.0",
#     "pillow>=10.0.0",
# ]
# ///
"""
Restore/enhance images using Gemini with automatic model fallback.

Usage:
    uv run restore.py --filename "output.png" -i damaged_photo.png
    uv run restore.py --filename "output.png" -i old_photo.png --prompt "restore colors and remove scratches"
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import generate_with_fallback, get_api_key, save_image

DEFAULT_PROMPT = (
    "Restore this image. Fix any damage, scratches, noise, or degradation. "
    "Enhance clarity and colors while preserving the original composition."
)


def main():
    parser = argparse.ArgumentParser(description="Restore/enhance images with Gemini (auto-fallback)")
    parser.add_argument("--filename", "-f", required=True, help="Output filename")
    parser.add_argument("--input-image", "-i", required=True, dest="input", help="Input image to restore")
    parser.add_argument("--prompt", "-p", default=DEFAULT_PROMPT, help="Custom restore instructions")
    parser.add_argument("--resolution", "-r", choices=["1K", "2K", "4K"], default="1K")
    parser.add_argument("--api-key", "-k", help="Gemini API key (overrides env)")
    args = parser.parse_args()

    from google import genai
    from google.genai import types
    from PIL import Image as PILImage

    client = genai.Client(api_key=get_api_key(args.api_key))
    output_path = Path(args.filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        img = PILImage.open(args.input)
        w, h = img.size
        print(f"Loaded: {args.input} ({w}x{h})")
    except Exception as e:
        print(f"Error loading '{args.input}': {e}", file=sys.stderr)
        sys.exit(1)

    # Auto-detect resolution
    resolution = args.resolution
    max_dim = max(w, h)
    if resolution == "1K" and max_dim > 0:
        if max_dim >= 3000:
            resolution = "4K"
        elif max_dim >= 1500:
            resolution = "2K"
        if resolution != args.resolution:
            print(f"Auto-detected resolution: {resolution} (max dim {max_dim})")

    contents = [img, args.prompt]
    print(f"Restoring image ({resolution})...")
    response, model_used = generate_with_fallback(
        client, types, contents, resolution=resolution,
    )
    save_image(response, output_path, model_used)


if __name__ == "__main__":
    main()
