"""Shared utilities for nanobanana-pro scripts."""

import os
import sys
from io import BytesIO
from pathlib import Path

# Fallback model chain
DEFAULT_MODELS = [
    "gemini-2.5-flash-image",
    "gemini-2.0-flash-exp-image-generation",
]


def get_api_key(provided_key: str | None = None) -> str:
    """Get API key from argument or environment."""
    if provided_key:
        return provided_key
    for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "NANOBANANA_GEMINI_API_KEY"):
        key = os.environ.get(var)
        if key:
            return key
    print("Error: No API key. Set GEMINI_API_KEY environment variable.", file=sys.stderr)
    sys.exit(1)


def get_fallback_models() -> list[str]:
    """Get model fallback chain."""
    env = os.getenv("NANOBANANA_FALLBACK_MODELS")
    if env:
        return [m.strip() for m in env.split(",") if m.strip()]
    return DEFAULT_MODELS.copy()


def generate_with_fallback(
    client,
    types,
    contents,
    resolution: str = "1K",
    models: list[str] | None = None,
) -> tuple:
    """Try generating with each model in the fallback chain.

    Returns (response, model_used) or exits on failure.
    """
    if models is None:
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
            # Check if response has image
            if response.parts:
                for part in response.parts:
                    if part.inline_data is not None:
                        return response, model_name
            print(f"  {model_name}: no image in response, trying next...")
            last_error = "No image in response"
        except Exception as e:
            print(f"  {model_name} failed: {e}")
            last_error = e
            continue

    print(f"Error: All models failed. Last error: {last_error}", file=sys.stderr)
    sys.exit(1)


def save_image(response, output_path: Path, model_used: str) -> None:
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
            else:
                image.convert("RGB").save(str(output_path), "PNG")

            full_path = output_path.resolve()
            print(f"\nImage saved: {full_path}")
            print(f"Model used: {model_used}")
            print(f"MEDIA: {full_path}")
            return

    print("Error: No image found in response.", file=sys.stderr)
    sys.exit(1)
