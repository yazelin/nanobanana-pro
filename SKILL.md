---
name: nanobanana-pro
description: Generate, edit, and restore images via Gemini image models with automatic model fallback.
version: 0.3.0
license: MIT
homepage: https://github.com/yazelin/nanobanana-py
author: yazelin
compatibility:
  platforms:
    - openclaw
    - ching-tech-os
metadata:
  openclaw:
    emoji: "🍌"
    requires:
      bins: ["uv"]
      env: ["GEMINI_API_KEY"]
    primaryEnv: GEMINI_API_KEY
  ctos:
    requires_app: ""
    mcp_servers: ""
---

# Nano Banana Pro — AI Image Generation with Fallback

Generate, edit, or restore images using Gemini image models. Automatically falls back through multiple models if one fails.

## Generate

```bash
uv run {baseDir}/scripts/generate.py --prompt "your image description" --filename "output.png" --resolution 1K
```

## Edit (single image)

```bash
uv run {baseDir}/scripts/generate.py --prompt "edit instructions" --filename "output.png" -i "/path/input.png" --resolution 2K
```

## Multi-image composition (up to 14 images)

```bash
uv run {baseDir}/scripts/generate.py --prompt "combine these into one scene" --filename "output.png" -i img1.png -i img2.png -i img3.png
```

## Restore / enhance

```bash
uv run {baseDir}/scripts/generate.py --restore --filename "output.png" -i "/path/damaged.png"
```

Custom restore prompt:

```bash
uv run {baseDir}/scripts/generate.py --restore --prompt "remove scratches and enhance colors" --filename "output.png" -i old_photo.png
```

## API key

- `GEMINI_API_KEY` env var
- Or set `skills."nanobanana-pro".apiKey` / `skills."nanobanana-pro".env.GEMINI_API_KEY` in `~/.openclaw/openclaw.json`

## Notes

- Resolutions: `1K` (default), `2K`, `4K`. Auto-detects from input image size.
- Models tried in order: `gemini-2.5-flash-image` → `gemini-2.0-flash-exp-image-generation` (configurable via `NANOBANANA_FALLBACK_MODELS`)
- Use timestamps in filenames: `yyyy-mm-dd-hh-mm-ss-name.png`.
- The script prints a `MEDIA:` line for OpenClaw to auto-attach on supported chat providers.
- Do not read the image back; report the saved path only.
