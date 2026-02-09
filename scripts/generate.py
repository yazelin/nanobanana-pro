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
    uv run generate.py --prompt "your image description" --filename "output.png" [--resolution 1K|2K|4K]

Multi-image editing (up to 14 images):
    uv run generate.py --prompt "combine these images" --filename "output.png" -i img1.png -i img2.png

Image restoration:
    uv run generate.py --restore --filename "output.png" -i damaged.png
"""

import argparse
import os
import sys
from io import BytesIO
from pathlib import Path

# Fallback model chain (configurable via NANOBANANA_FALLBACK_MODELS env var)
DEFAULT_FALLBACK_MODELS = [
    "gemini-2.5-flash-image",
    "gemini-2.0-flash-exp-image-generation",
]

DEFAULT_RESTORE_PROMPT = (
    "Restore this image. Fix any damage, scratches, noise, or degradation. "
    "Enhance clarity and colors while preserving the original composition."
)


def get_api_key(provided_key: str | None) -> str | None:
    if provided_key:
        return provided_key
    for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "NANOBANANA_GEMINI_API_KEY"):
        key = os.environ.get(var)
        if key:
            return key
    return None


def get_fallback_models() -> list[str]:
    env = os.getenv("NANOBANANA_FALLBACK_MODELS")
    if env:
        return [m.strip() for m in env.split(",") if m.strip()]
    return DEFAULT_FALLBACK_MODELS.copy()


def generate_with_fallback(client, types, contents, resolution: str = "1K"):
    """Try each model in the fallback chain until one returns an image."""
    models = get_fallback_models()
    last_error = None

    for model_name in models:
        print(f"Trying model: {model_name}...")
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                    image_config=types.ImageConfig(image_size=resolution),
                ),
            )
            if response.parts:
                for part in response.parts:
                    if part.inline_data is not None:
                        print(f"  ✓ Success with {model_name}")
                        return response, model_name
            print(f"  {model_name}: no image in response, trying next...")
            last_error = "No image in response"
        except Exception as e:
            print(f"  {model_name} failed: {e}")
            last_error = e
            continue

    print(f"Error: All models failed. Last error: {last_error}", file=sys.stderr)
    sys.exit(1)


def save_response_image(response, output_path: Path, model_used: str):
    """Extract image from response and save as PNG."""
    from PIL import Image as PILImage

    for part in response.parts:
        if part.text is not None:
            print(f"Model response: {part.text}")
        elif part.inline_data is not None:
            image_data = part.inline_data.data
            if isinstance(image_data, str):
                import base64
                image_data = base64.b64decode(image_data)

            image = PILImage.open(BytesIO(image_data))
            if image.mode == "RGBA":
                rgb = PILImage.new("RGB", image.size, (255, 255, 255))
                rgb.paste(image, mask=image.split()[3])
                rgb.save(str(output_path), "PNG")
            elif image.mode == "RGB":
                image.save(str(output_path), "PNG")
            else:
                image.convert("RGB").save(str(output_path), "PNG")

            full_path = output_path.resolve()
            print(f"\nImage saved: {full_path}")
            print(f"Model used: {model_used}")
            print(f"MEDIA: {full_path}")
            return

    print("Error: No image was generated in the response.", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Generate/edit/restore images using Gemini with auto model fallback"
    )
    parser.add_argument("--prompt", "-p", help="Image description or edit instructions")
    parser.add_argument("--filename", "-f", required=True, help="Output filename (e.g., output.png)")
    parser.add_argument("--input-image", "-i", action="append", dest="input_images", metavar="IMAGE",
                        help="Input image path(s) for editing/composition (up to 14)")
    parser.add_argument("--resolution", "-r", choices=["1K", "2K", "4K"], default="1K",
                        help="Output resolution (default: 1K)")
    parser.add_argument("--restore", action="store_true",
                        help="Restore/enhance mode (auto-sets prompt if not provided)")
    parser.add_argument("--api-key", "-k", help="Gemini API key (overrides GEMINI_API_KEY env var)")
    args = parser.parse_args()

    # Validate
    if args.restore and not args.input_images:
        print("Error: --restore requires at least one --input-image (-i)", file=sys.stderr)
        sys.exit(1)
    if not args.restore and not args.prompt:
        print("Error: --prompt is required (unless using --restore)", file=sys.stderr)
        sys.exit(1)

    api_key = get_api_key(args.api_key)
    if not api_key:
        print("Error: No API key. Set GEMINI_API_KEY or use --api-key.", file=sys.stderr)
        sys.exit(1)

    from google import genai
    from google.genai import types
    from PIL import Image as PILImage

    client = genai.Client(api_key=api_key)
    output_path = Path(args.filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine prompt
    prompt = args.prompt or DEFAULT_RESTORE_PROMPT

    # Load input images
    input_images = []
    resolution = args.resolution
    if args.input_images:
        if len(args.input_images) > 14:
            print(f"Error: Too many images ({len(args.input_images)}). Max 14.", file=sys.stderr)
            sys.exit(1)

        max_dim = 0
        for img_path in args.input_images:
            try:
                img = PILImage.open(img_path)
                input_images.append(img)
                w, h = img.size
                max_dim = max(max_dim, w, h)
                print(f"Loaded input: {img_path} ({w}x{h})")
            except Exception as e:
                print(f"Error loading '{img_path}': {e}", file=sys.stderr)
                sys.exit(1)

        # Auto-detect resolution from input
        if resolution == "1K" and max_dim > 0:
            if max_dim >= 3000:
                resolution = "4K"
            elif max_dim >= 1500:
                resolution = "2K"
            if resolution != args.resolution:
                print(f"Auto-detected resolution: {resolution} (max dim {max_dim})")

    # Build contents
    if input_images:
        contents = [*input_images, prompt]
        mode = "Restoring" if args.restore else f"Editing {len(input_images)} image(s)"
    else:
        contents = prompt
        mode = "Generating"

    print(f"{mode} ({resolution})...")
    response, model_used = generate_with_fallback(client, types, contents, resolution)
    save_response_image(response, output_path, model_used)


if __name__ == "__main__":
    main()
