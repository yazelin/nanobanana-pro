"""Shared utilities for nanobanana-pro scripts. Zero external dependencies."""

import base64
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# Fallback model chain
DEFAULT_MODELS = [
    "gemini-2.5-flash-image",
    "gemini-2.0-flash-exp-image-generation",
]


def get_api_key(provided_key: str | None = None) -> str:
    if provided_key:
        return provided_key
    for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "NANOBANANA_GEMINI_API_KEY"):
        key = os.environ.get(var)
        if key:
            return key
    print("Error: No API key. Set GEMINI_API_KEY environment variable.", file=sys.stderr)
    sys.exit(1)


def get_fallback_models() -> list[str]:
    env = os.getenv("NANOBANANA_FALLBACK_MODELS")
    if env:
        return [m.strip() for m in env.split(",") if m.strip()]
    return DEFAULT_MODELS.copy()


def _build_request(prompt: str, model: str, resolution: str = "1K",
                    input_images_b64: list[tuple[str, str]] | None = None) -> dict:
    """Build Gemini REST API request body.

    input_images_b64: list of (base64_data, mime_type) tuples
    """
    parts = []
    if input_images_b64:
        for data, mime in input_images_b64:
            parts.append({"inlineData": {"mimeType": mime, "data": data}})
    parts.append({"text": prompt})

    return {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "responseModalities": ["Image"],
            "imageConfig": {"imageSize": resolution},
        },
    }


def load_image_as_base64(path: str) -> tuple[str, str]:
    """Load image file and return (base64_data, mime_type)."""
    p = Path(path)
    if not p.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        sys.exit(1)

    ext = p.suffix.lower()
    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp"}
    mime = mime_map.get(ext, "image/png")

    with open(p, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return data, mime


def generate_with_fallback(
    api_key: str,
    prompt: str,
    resolution: str = "1K",
    input_images_b64: list[tuple[str, str]] | None = None,
    models: list[str] | None = None,
) -> tuple[dict, str]:
    """Try generating with each model. Returns (response_json, model_used)."""
    if models is None:
        models = get_fallback_models()

    last_error = None
    for model in models:
        print(f"Trying model: {model}...")
        url = f"{API_BASE}/{model}:generateContent?key={api_key}"
        body = _build_request(prompt, model, resolution, input_images_b64)
        data = json.dumps(body).encode()
        req = urllib.request.Request(url, data=data,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())

            # Check for image in response
            for cand in result.get("candidates", []):
                for part in cand.get("content", {}).get("parts", []):
                    if "inlineData" in part:
                        return result, model
            print(f"  {model}: no image in response, trying next...")
            last_error = "No image in response"
        except urllib.error.HTTPError as e:
            err_body = e.read().decode() if e.fp else str(e)
            print(f"  {model} failed: HTTP {e.code} - {err_body[:200]}")
            last_error = err_body
        except Exception as e:
            print(f"  {model} failed: {e}")
            last_error = str(e)

    print(f"Error: All models failed. Last: {last_error}", file=sys.stderr)
    sys.exit(1)


def save_image(result: dict, output_path: Path, model_used: str) -> None:
    """Extract image from API response and save."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    for cand in result.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            if "text" in part:
                print(f"Model response: {part['text']}")
            if "inlineData" in part:
                img_data = base64.b64decode(part["inlineData"]["data"])
                with open(output_path, "wb") as f:
                    f.write(img_data)
                full = output_path.resolve()
                print(f"\nImage saved: {full}")
                print(f"Model used: {model_used}")
                print(f"MEDIA: {full}")
                return

    print("Error: No image found in response.", file=sys.stderr)
    sys.exit(1)
