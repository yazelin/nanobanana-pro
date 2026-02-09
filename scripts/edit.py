#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "google-genai>=1.0.0",
#     "pillow>=10.0.0",
# ]
# ///
"""
Edit images using Gemini with automatic model fallback.

Usage:
    uv run edit.py --prompt "edit instructions" --filename "output.png" -i input.png
    uv run edit.py --prompt "combine these" --filename "output.png" -i img1.png -i img2.png
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import generate_with_fallback, get_api_key, save_image


def main():
    parser = argparse.ArgumentParser(description="Edit images with Gemini (auto-fallback)")
    parser.add_argument("--prompt", "-p", required=True, help="Edit instructions")
    parser.add_argument("--filename", "-f", required=True, help="Output filename")
    parser.add_argument("--input-image", "-i", action="append", dest="inputs", required=True,
                        help="Input image(s), up to 14")
    parser.add_argument("--resolution", "-r", choices=["1K", "2K", "4K"], default="1K")
    parser.add_argument("--api-key", "-k", help="Gemini API key (overrides env)")
    args = parser.parse_args()

    if len(args.inputs) > 14:
        print(f"Error: Too many images ({len(args.inputs)}). Max 14.", file=sys.stderr)
        sys.exit(1)

    from google import genai
    from google.genai import types
    from PIL import Image as PILImage

    client = genai.Client(api_key=get_api_key(args.api_key))
    output_path = Path(args.filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load input images
    images = []
    max_dim = 0
    for img_path in args.inputs:
        try:
            img = PILImage.open(img_path)
            images.append(img)
            w, h = img.size
            max_dim = max(max_dim, w, h)
            print(f"Loaded: {img_path} ({w}x{h})")
        except Exception as e:
            print(f"Error loading '{img_path}': {e}", file=sys.stderr)
            sys.exit(1)

    # Auto-detect resolution from input if default
    resolution = args.resolution
    if resolution == "1K" and max_dim > 0:
        if max_dim >= 3000:
            resolution = "4K"
        elif max_dim >= 1500:
            resolution = "2K"
        if resolution != args.resolution:
            print(f"Auto-detected resolution: {resolution} (max dim {max_dim})")

    contents = [*images, args.prompt]
    print(f"Editing {len(images)} image(s) ({resolution})...")
    response, model_used = generate_with_fallback(
        client, types, contents, resolution=resolution,
    )
    save_image(response, output_path, model_used)


if __name__ == "__main__":
    main()
