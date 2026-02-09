#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Edit images using Gemini with automatic model fallback.
Zero external dependencies — uses only Python stdlib.

Usage:
    python3 edit.py --prompt "edit instructions" --filename "output.png" -i input.png
    python3 edit.py --prompt "combine these" --filename "output.png" -i img1.png -i img2.png
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import generate_with_fallback, get_api_key, load_image_as_base64, save_image


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

    api_key = get_api_key(args.api_key)
    output_path = Path(args.filename)

    images_b64 = []
    for img_path in args.inputs:
        data, mime = load_image_as_base64(img_path)
        print(f"Loaded: {img_path}")
        images_b64.append((data, mime))

    print(f"Editing {len(images_b64)} image(s) ({args.resolution})...")
    result, model_used = generate_with_fallback(
        api_key, args.prompt, args.resolution, input_images_b64=images_b64,
    )
    save_image(result, output_path, model_used)


if __name__ == "__main__":
    main()
