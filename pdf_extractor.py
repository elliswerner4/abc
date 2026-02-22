"""PDF → GPT-4o Vision extraction of racking layout data."""

import base64
import io
import json
import os
import re
import tempfile
from pathlib import Path

import httpx
from pdf2image import convert_from_bytes
from PIL import Image


VISION_PROMPT = """You are a warehouse racking layout analyst. Analyze these PDF pages of a racking layout drawing and extract all relevant data.

The PDF typically contains:
1. **Plan View (bird's eye)**: Shows a grid of letters (A, B, C, etc.) representing bay types arranged in rows. Count the bays carefully — each letter cell is one bay. Rows are back-to-back pairs of bays separated by aisles.
2. **Elevation Views (side views)**: Show the rack profile with beam levels, heights, and dimensions. Each bay type (A, B, C) usually has its own elevation drawing.
3. **Title Block / Notes**: Project name, client, dimensions, pallet info.

Extract and return a JSON object with EXACTLY this structure:
{
  "project_name": "string — project name from title block",
  "client": "string — client/company name",
  "rack_style": "teardrop" or "structural",
  "frame_height": number in inches (total upright height),
  "frame_depth": number in inches (e.g. 42, 44, 48),
  "pallet_size": "string e.g. 40x48",
  "bay_types": [
    {
      "label": "A",
      "bays": number — total bays of this type across ALL rows,
      "rows": number — how many rows contain this bay type,
      "tunnels": number — tunnel bays for this type (usually 0),
      "beam_levels": number — count of beam levels from the elevation view,
      "beam_length": number in inches — the beam span (bay width)
    }
  ],
  "notes": "any other relevant observations"
}

CRITICAL COUNTING RULES:
- **Bays**: Count each letter in the plan view grid. A bay is one unit cell. If you see "AAAA" that's 4 bays of type A in that segment.
- **Rows**: A row is a continuous line of bays. Back-to-back rows share frames. Count how many distinct rows contain each bay type.
- **Beam levels**: Count the horizontal beam lines in the elevation view (NOT including the floor). Each pair of beams (front + back) holds pallets at that level.
- **Beam length**: The horizontal span in the elevation or plan view, in inches.
- **Tunnels**: Cross-aisles that cut through rows. They add extra frames but have fewer beam levels.
- **Frame height**: The total height of the upright frame, in inches.
- **Frame depth**: The depth of the frame (front to back), in inches. Common: 42", 44", 48".

Be precise with counts. Double-check by looking at the total pallet positions if shown on the drawing.
Return ONLY valid JSON, no markdown fences."""


async def extract_from_pdf(pdf_bytes: bytes, api_key: str) -> dict:
    """Convert PDF to images, send to GPT-4o vision, return parsed extraction."""

    # Convert PDF pages to images
    images = convert_from_bytes(pdf_bytes, dpi=200, fmt="png")

    # Encode images as base64
    image_contents = []
    for i, img in enumerate(images):
        buf = io.BytesIO()
        # Resize if very large (keep under 2000px on longest side for API)
        max_dim = 2000
        if max(img.size) > max_dim:
            ratio = max_dim / max(img.size)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
        img.save(buf, format="PNG", optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        image_contents.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{b64}",
                "detail": "high",
            },
        })

    # Build messages
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": VISION_PROMPT},
                *image_contents,
            ],
        }
    ]

    # Call GPT-4o
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o",
                "messages": messages,
                "max_tokens": 4096,
                "temperature": 0.1,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    content = data["choices"][0]["message"]["content"]

    # Strip markdown fences if present
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

    extracted = json.loads(content)
    return extracted
