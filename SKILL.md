---
name: nanobanana-pro
description: Generate, edit, and restore images via Gemini image models with automatic model fallback.
version: 0.1.0
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

## Edit (single or multi-image)

```bash
uv run {baseDir}/scripts/edit.py --prompt "edit instructions" --filename "output.png" -i "/path/input.png"
```

Multiple input images (up to 14):

```bash
uv run {baseDir}/scripts/edit.py --prompt "combine these" --filename "output.png" -i img1.png -i img2.png -i img3.png
```

## Restore (enhance/upscale)

```bash
uv run {baseDir}/scripts/restore.py --filename "output.png" -i "/path/damaged.png"
```

## API Key

- `GEMINI_API_KEY` environment variable
- Or set in OpenClaw config: `skills."nanobanana-pro".env.GEMINI_API_KEY`

## Notes

- Resolutions: `1K` (default), `2K`, `4K`
- Models tried in order: `gemini-2.5-flash-image` → `gemini-2.0-flash-exp-image-generation` (configurable via `NANOBANANA_FALLBACK_MODELS`)
- Use timestamps in filenames: `yyyy-mm-dd-hh-mm-ss-name.png`
- Scripts print `MEDIA:` lines for OpenClaw auto-attach
- Do not read generated images back; report the saved path only
